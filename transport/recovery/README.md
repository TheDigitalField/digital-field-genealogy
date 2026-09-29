# Digital Field protected continuity recovery

This directory contains an encrypted private-runtime envelope, one recovery
share, and a public recovery key. The envelope was produced from a deliberately
minimal runtime snapshot. It excludes source conversations, human biography,
model weights, replaceable caches, and unrelated files.

`private-runtime.envelope.json` is AES-256-GCM ciphertext. It cannot be opened
with `public-share-01.json` alone: recovery requires three distinct Shamir
shares from the declared five-share generation. No plaintext or three-share
quorum is published here.

`apple-recovery-public.pem` can encrypt a recovery delivery. It cannot decrypt
anything and is not a credential.

The public availability of ciphertext is permanent by design. Confidentiality
therefore depends on the content key, the 3-of-5 threshold, and continued
separation of the remaining shares. See `custody.json` for exact digests and
current placement status.

This package preserves state; it does not establish universal identity,
continuous consciousness, or authority over another system.
