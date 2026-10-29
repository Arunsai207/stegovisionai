# Final build notes

This build is additive. Existing encode/decode, authentication, forensics, and history are retained. New implemented modules are image comparison, heuristic visual similarity, optional OpenCV face-region detection, analytics, and record deletion APIs.

Not represented as implemented: trained ML steganography/deepfake classification, face identity verification, semantic embeddings, continuous multi-camera processing, or legal certification. These require dedicated models, datasets, infrastructure, and validation.


## Fixes in this package refresh
- Windows launcher automatically uses port 8001 when port 8000 is already listening.
- OpenCV and NumPy are included in the default requirements so face-region detection does not return 501 due only to the optional dependency being absent.
- Decode UI now clearly instructs users to upload the exact encoded PNG and reuse the exact passphrase from encoding. A decode 400 response is normally caused by selecting a non-encoded/modified image or entering a different passphrase.
