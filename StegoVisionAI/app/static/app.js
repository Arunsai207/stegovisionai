const $ = (id) => document.getElementById(id);
let token = localStorage.getItem("sv_token") || "";
let currentUser = null;
let toastTimer;
let lastEncodedFile = null;
let decodeFileOverride = null;

function authHeaders() { return token ? {Authorization: `Bearer ${token}`} : {}; }
async function api(url, options = {}) {
  const headers = {...authHeaders(), ...(options.headers || {})};
  const response = await fetch(url, {...options, headers});
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try { const data = await response.json(); message = data.detail || data.message || message; } catch {}
    if (response.status === 401 && token) signOut(false);
    throw new Error(message);
  }
  return response;
}
function showToast(message, type="success") {
  const el=$("toast"); el.textContent=message; el.className=`toast ${type}`;
  clearTimeout(toastTimer); toastTimer=setTimeout(()=>el.classList.add("hidden"),4500);
}
function authError(message) { $("authError").textContent=message; $("authError").classList.remove("hidden"); }
function setAuthMode(mode) {
  const register = mode === "register";
  $("loginForm").classList.toggle("hidden", register);
  $("registerForm").classList.toggle("hidden", !register);
  $("authTitle").textContent = register ? "Create your account." : "Welcome back.";
  $("authSubtitle").textContent = register ? "Set up your secure forensic workspace." : "Sign in to continue to your forensic workspace.";
  $("switchText").textContent = register ? "Already have an account?" : "New to StegoVision AI?";
  $("switchAuth").textContent = register ? "Sign in" : "Create an account";
  $("authError").classList.add("hidden");
}
$("switchAuth").addEventListener("click",()=>setAuthMode($("registerForm").classList.contains("hidden")?"register":"login"));
function showWelcome(message) {
  $("welcomeText").textContent=message;
  $("welcomeBanner").classList.remove("hidden");
}
$("closeWelcome").addEventListener("click",()=>$("welcomeBanner").classList.add("hidden"));
function showApp(user, welcome) {
  currentUser=user; $("authScreen").classList.add("hidden");
  $("avatar").textContent=(user.name||user.email||"?").trim().charAt(0).toUpperCase();
  if(welcome) showWelcome(welcome);
  navigate("overview");
  loadHistory().catch(()=>{});
}
function signOut(showMessage=true) {
  token=""; currentUser=null; localStorage.removeItem("sv_token");
  $("authScreen").classList.remove("hidden"); setAuthMode("login");
  if(showMessage) showToast("You have signed out.","success");
}
$("loginForm").addEventListener("submit",async(e)=>{
  e.preventDefault(); $("authError").classList.add("hidden");
  try {
    const r=await fetch("/api/auth/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:$("loginEmail").value,password:$("loginPassword").value})});
    const d=await r.json(); if(!r.ok) throw new Error(d.detail||"Sign-in failed.");
    token=d.token; localStorage.setItem("sv_token",token); showApp(d.user,d.welcome);
  } catch(err){authError(err.message);}
});
$("registerForm").addEventListener("submit",async(e)=>{
  e.preventDefault(); $("authError").classList.add("hidden");
  if($("registerPassword").value!==$("registerConfirm").value){authError("The passwords do not match.");return;}
  try {
    const r=await fetch("/api/auth/register",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:$("registerName").value,email:$("registerEmail").value,password:$("registerPassword").value})});
    const d=await r.json(); if(!r.ok) throw new Error(d.detail||"Registration failed.");
    token=d.token; localStorage.setItem("sv_token",token); showApp(d.user,d.welcome);
  } catch(err){authError(err.message);}
});
$("logoutBtn").addEventListener("click",()=>signOut(true));
function navigate(page) {
  document.querySelectorAll(".page").forEach(p=>p.classList.toggle("active",p.id===`page-${page}`));
  document.querySelectorAll(".nav-item").forEach(b=>b.classList.toggle("active",b.dataset.page===page));
  const labels={overview:"Overview",encode:"Encode message",decode:"Extract message",forensics:"Image forensics",advanced:"Advanced lab",history:"Analysis history"};
  if(page==="advanced"){loadAnalytics().catch(()=>{});}
  $("topTitle").textContent=labels[page]||"Overview";
  $("sidebar").classList.remove("open");
  if(page==="history") loadHistory().catch(e=>showToast(e.message,"error"));
}
document.querySelectorAll("[data-page]").forEach(b=>b.addEventListener("click",()=>navigate(b.dataset.page)));
document.querySelectorAll("[data-goto]").forEach(b=>b.addEventListener("click",()=>navigate(b.dataset.goto)));
$("menuBtn").addEventListener("click",()=>$("sidebar").classList.toggle("open"));
function fileLabel(input,label){$(input).addEventListener("change",()=>{if(input==="decodeFile") decodeFileOverride=null; $(label).textContent=$(input).files[0]?.name||"No file selected";});}
fileLabel("encodeFile","encodeFileName"); fileLabel("decodeFile","decodeFileName"); fileLabel("forensicFile","forensicFileName");
function setBusy(button,busy,label) { const el=$(button); el.disabled=busy; el.dataset.original ||= el.innerHTML; el.innerHTML=busy?"Processing…":(label||el.dataset.original); el.style.opacity=busy?".65":"1"; }
$("encodeBtn").addEventListener("click",async()=>{
  const file=$("encodeFile").files[0], message=$("secretMessage").value, passphrase=$("encodePass").value;
  if(!file||!message.trim()||!passphrase){showToast("Choose an image and enter a message and passphrase.","error");return;}
  const fd=new FormData();fd.append("image",file);fd.append("message",message);fd.append("passphrase",passphrase);
  setBusy("encodeBtn",true);
  try{
    const r=await api("/api/encode",{method:"POST",body:fd});
    const blob=await r.blob();
    const name=(file.name.replace(/\.[^.]+$/,"").trim()||"image")+"_stegovision.png";
    // Verify the exact bytes returned by the encoder before presenting them as ready.
    const verifyForm=new FormData();
    verifyForm.append("image",new File([blob],name,{type:"image/png"}));
    verifyForm.append("passphrase",passphrase);
    const verifyResponse=await api("/api/decode",{method:"POST",body:verifyForm});
    const verifyData=await verifyResponse.json();
    if(verifyData.message!==message) throw new Error("Round-trip verification failed: the extracted text differs from the original. The output was not marked as ready.");

    lastEncodedFile=new File([blob],name,{type:"image/png"});
    const url=URL.createObjectURL(blob);
    $("encodeResult").className="result-success";
    $("encodeResult").innerHTML=`<b>✓ Encoded PNG verified</b><p>The saved PNG bytes passed an encode → decode check and the recovered text matches your input. Download this file for later extraction.</p><button class="primary-btn" id="downloadEncoded">Download verified PNG ↗</button><button class="secondary-btn" id="openExtractEncoded">Extract this PNG now</button><p class="microcopy" id="verifyEncodedResult" aria-live="polite">✓ Round-trip verification passed.</p>`;
    $("downloadEncoded").addEventListener("click",()=>{const a=document.createElement("a");a.href=url;a.download=name;a.click();});
    $("openExtractEncoded").addEventListener("click",()=>{
      decodeFileOverride=lastEncodedFile;
      $("decodeFileName").textContent=name+" (verified in this session)";
      $("decodePass").value=passphrase;
      navigate("decode");
      showToast("Verified encoded PNG selected. Click Extract message.");
    });
    showToast("Encoding and round-trip verification succeeded.");
  }catch(e){
    $("encodeResult").className="result-error";
    $("encodeResult").textContent="Encoding or verification failed: "+e.message;
    showToast(e.message,"error");
  }finally{setBusy("encodeBtn",false);}
});
$("decodeBtn").addEventListener("click",async()=>{
  const file=decodeFileOverride||$("decodeFile").files[0],passphrase=$("decodePass").value;
  if(!file||!passphrase){showToast("Choose the encoded PNG (not the original cover image) and enter its passphrase.","error");return;}
  const fd=new FormData();fd.append("image",file);fd.append("passphrase",passphrase);setBusy("decodeBtn",true);
  try{
    const r=await api("/api/decode",{method:"POST",body:fd});const d=await r.json();
    $("decodeResult").className="result-success";$("decodeResult").innerHTML="";
    const title=document.createElement("b");title.textContent="✓ Message extracted";
    const p=document.createElement("p");p.textContent=d.message;
    const copy=document.createElement("button");copy.className="secondary-btn";copy.textContent="Copy message";
    copy.addEventListener("click",async()=>{await navigator.clipboard.writeText(d.message);showToast("Message copied.");});
    $("decodeResult").append(title,p,copy);showToast("Message extracted successfully.");
  }catch(e){
    $("decodeResult").className="result-error";$("decodeResult").textContent="Extraction failed: "+e.message+" If you selected the original cover image, return to Encode and use Download verified PNG, or choose the previously downloaded *_stegovision.png file. Use the exact same passphrase.";
    showToast(e.message,"error");
  }finally{setBusy("decodeBtn",false);}
});
$("analyzeBtn").addEventListener("click",async()=>{
  const file=$("forensicFile").files[0];if(!file){showToast("Choose an image first.","error");return;}
  const fd=new FormData();fd.append("image",file);setBusy("analyzeBtn",true);
  try{const r=await api("/api/forensics",{method:"POST",body:fd});const d=await r.json();renderForensics(d);showToast("Image analysis completed.");loadHistory().catch(()=>{});
  }catch(e){showToast(e.message,"error");}finally{setBusy("analyzeBtn",false);}
});
function renderForensics(d){
  const root=$("forensicResult");root.classList.remove("hidden");root.className="forensic-results";
  root.innerHTML=`<div class="result-metrics"><div class="metric"><small>FORMAT</small><b id="mFormat"></b></div><div class="metric"><small>DIMENSIONS</small><b id="mDimensions"></b></div><div class="metric"><small>FILE SIZE</small><b id="mSize"></b></div><div class="metric"><small>PIXEL ENTROPY</small><b id="mEntropy"></b></div></div><div class="hash-box"><small>SHA-256 · FILE INTEGRITY HASH</small><code id="mHash"></code></div><div class="panel"><div class="panel-head"><div><span class="step">REPORT</span><h3>Analysis findings</h3></div><span class="panel-tag" id="mVerdict"></span></div><div id="findingList" class="findings"></div></div>`;
  $("mFormat").textContent=d.format;$("mDimensions").textContent=`${d.width} × ${d.height}`;$("mSize").textContent=(d.bytes/1024).toFixed(1)+" KB";$("mEntropy").textContent=d.entropy??"N/A";$("mHash").textContent=d.sha256;$("mVerdict").textContent=d.verdict;
  const list=$("findingList");d.findings.forEach(f=>{const item=document.createElement("div");item.className=`finding ${f.level}-level`;const b=document.createElement("b");b.textContent=f.title;const p=document.createElement("p");p.textContent=f.detail;item.append(b,p);list.append(item);});
  if(d.metadata_keys?.length){const item=document.createElement("div");item.className="finding info-level";const b=document.createElement("b");b.textContent="Metadata fields";const p=document.createElement("p");p.textContent=d.metadata_keys.join(", ");item.append(b,p);list.append(item);}
}
async function loadHistory(){
  if(!token)return;const r=await api("/api/history");const d=await r.json();$("statAnalyses").textContent=d.items.length;
  const root=$("historyTable");if(!d.items.length){root.innerHTML='<div class="empty-result"><div class="empty-symbol">▤</div><b>No analyses yet</b><p>Inspect an image to create your first history entry.</p></div>';return;}
  const table=document.createElement("table");table.className="history-table";table.innerHTML="<thead><tr><th>FILE / TYPE</th><th>SHA-256</th><th>DATE</th><th>ACTION</th></tr></thead>";const tbody=document.createElement("tbody");
  d.items.forEach(item=>{const tr=document.createElement("tr");const name=document.createElement("td");name.textContent=`${item.filename} · ${(item.kind||"forensics").replaceAll("_"," ")}`;const hash=document.createElement("td");hash.className="hash-short";hash.textContent=item.sha256?item.sha256.slice(0,16)+"…":"—";hash.title=item.sha256||"";const date=document.createElement("td");date.textContent=item.created_at;const action=document.createElement("td");const del=document.createElement("button");del.className="delete-record";del.textContent="Delete";del.addEventListener("click",async()=>{if(!confirm(`Delete record for ${item.filename}? This cannot be undone.`))return;try{const rr=await api(`/api/history/${item.id}`,{method:"DELETE"});const dd=await rr.json();if(!rr.ok)throw new Error(dd.detail||"Delete failed.");await loadHistory();await loadAnalytics().catch(()=>{});showToast("Record deleted.");}catch(e){showToast(e.message,"error");}});action.append(del);tr.append(name,hash,date,action);tbody.append(tr);});table.append(tbody);root.replaceChildren(table);
}
$("refreshHistory").addEventListener("click",()=>loadHistory().then(()=>showToast("History refreshed.")).catch(e=>showToast(e.message,"error")));
$("clearHistory").addEventListener("click",async()=>{if(!confirm("Delete every analysis record in your account? This cannot be undone."))return;try{const r=await api("/api/history",{method:"DELETE"});const d=await r.json();if(!r.ok)throw new Error(d.detail||"Clear failed.");await loadHistory();await loadAnalytics().catch(()=>{});showToast(`${d.deleted_count} records deleted.`);}catch(e){showToast(e.message,"error");}});

function esc(value){return String(value??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
function line(label,value){return `<div class="result-line"><span>${esc(label)}</span><b>${esc(value)}</b></div>`;}
function showAdvancedError(id,msg){$(id).className="advanced-result";$(id).textContent=msg;}
$("faceFile").addEventListener("change",()=>$("faceFileName").textContent=$("faceFile").files[0]?.name||"No file selected");
$("compareBtn").addEventListener("click",async()=>{
 const a=$("compareA").files[0],b=$("compareB").files[0];if(!a||!b){showToast("Choose both images first.","error");return;}
 const fd=new FormData();fd.append("image_a",a);fd.append("image_b",b);setBusy("compareBtn",true);
 try{const r=await api("/api/compare",{method:"POST",body:fd});const d=await r.json();if(!r.ok)throw new Error(d.detail||"Comparison failed.");
  const root=$("compareResult");root.className="advanced-result";root.innerHTML=line("Identical files",d.identical_files?"Yes":"No")+line("Same dimensions",d.same_dimensions?"Yes":"No")+line("Visual similarity (coarse)",`${d.visual_similarity}%`)+(d.mean_absolute_channel_difference!==undefined?line("Mean channel difference",d.mean_absolute_channel_difference):"")+`<p>${(d.differences||[]).map(esc).join("<br>")}</p><p class="microcopy">${(d.limitations||[]).map(esc).join(" ")}</p>`;showToast("Comparison completed.");loadHistory().catch(()=>{});loadAnalytics().catch(()=>{});
 }catch(e){showAdvancedError("compareResult",e.message);showToast(e.message,"error");}finally{setBusy("compareBtn",false);}
});
$("similarityBtn").addEventListener("click",async()=>{
 const a=$("compareA").files[0],b=$("compareB").files[0];if(!a||!b){showToast("Choose both images in Dual-image comparison first.","error");return;}
 const fd=new FormData();fd.append("image_a",a);fd.append("image_b",b);
 try{const r=await api("/api/similarity",{method:"POST",body:fd});const d=await r.json();if(!r.ok)throw new Error(d.detail||"Similarity analysis failed.");const root=$("similarityResult");root.className="advanced-result";root.innerHTML=`<div class="metric"><small>COARSE COLOR SIMILARITY</small><b>${esc(d.score)}%</b></div><p>${esc(d.interpretation)}</p><p class="microcopy">Method: ${esc(d.method)}</p>`;}catch(e){showAdvancedError("similarityResult",e.message);showToast(e.message,"error");}
});
$("faceBtn").addEventListener("click",async()=>{
 const file=$("faceFile").files[0];if(!file){showToast("Choose an image first.","error");return;}const fd=new FormData();fd.append("image",file);setBusy("faceBtn",true);
 try{const r=await api("/api/faces/detect",{method:"POST",body:fd});const d=await r.json();if(!r.ok)throw new Error(d.detail||"Face detection failed.");const root=$("faceResult");root.className="advanced-result";root.innerHTML=line("Detected face regions",d.face_count)+`<p>Detector: ${esc(d.detector)}</p><p>${(d.limitations||[]).map(esc).join(" ")}</p>`+(d.faces||[]).map((f,i)=>`<div class="result-line"><span>Face region ${i+1}</span><b>x ${f.x}, y ${f.y}, ${f.width}×${f.height}</b></div>`).join("");showToast("Face detection completed.");loadHistory().catch(()=>{});loadAnalytics().catch(()=>{});
 }catch(e){showAdvancedError("faceResult",e.message);showToast(e.message,"error");}finally{setBusy("faceBtn",false);}
});
async function loadAnalytics(){if(!token)return;const r=await api("/api/analytics");const d=await r.json();if(!r.ok)throw new Error(d.detail||"Could not load analytics.");const root=$("analyticsResult");root.className="advanced-result";root.innerHTML=line("Total saved analyses",d.total_analyses)+Object.entries(d.by_type||{}).map(([k,v])=>line(k.replaceAll("_"," "),v)).join("")||"No analyses recorded yet.";}
$("refreshAnalytics").addEventListener("click",()=>loadAnalytics().then(()=>showToast("Analytics refreshed.")).catch(e=>showToast(e.message,"error")));

(async function init(){
  if(!token){$("authScreen").classList.remove("hidden");return;}
  try{const r=await api("/api/auth/me");const d=await r.json();showApp(d.user,d.welcome);}
  catch{$("authScreen").classList.remove("hidden");}
})();
