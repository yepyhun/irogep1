# Fejlesztési Motor v1.0 — Skeleton

**Röviden, embernek:**  
Ez egy Windows-első segédprogram váza. Később a böngészős LLM-től kapott „Patch Package” csomagot itt illeszted be, a program pedig biztonságosan lefuttatja a vizsgálatokat, és kimenetet készít.

**Operátornak (váz):**  
- `runner/`: a parancssori orchestrator vázai  
- `gates/`: Build Gate modulok helye (lint/compile/spec/smoke/pack/security)  
- `sandbox/`: Windows Sandbox profilok és indítóscriptek helye  
- `gui/`: asztali GUI projekt (Windows) helye  
- `0_SYSTEM/`: audit- és export-mappák (append-only)  
- `PRPs/`: spec sablonok és példányok  
- `EXAMPLES/`: golden/anti minták  
- `1_PROJECTS/minta_projekt/`: mintaprojekt (src/tests/dist)

*Ez csak a projekt váza. Nincs implementált üzleti logika.*
