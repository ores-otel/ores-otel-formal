# Ores OTel redaction-before-export reference

Run `node formal/attolang/model_check.mjs`. The suite exhaustively explores its small bounded abstraction, demands reachable positive/adversarial witnesses, and tests that an unsafe mutant is detected.

`telemetry_policy.atto` is a draft AttoLang **source-level reference policy**, not a compiled or executed guest. The Node checker does not parse or execute it and does not call production APIs.

This supplements, but does not replace, the existing Quint telemetry_pipeline proofs. It cannot prove product exporter behavior, secret scanners, production redaction correctness, or network confidentiality.

To promote beyond model-only evidence, add an actual product trace/refinement adapter and run compiled `.atto` guests with nonzero executed steps on the Java, LLVM, Wasm, Forge and .NET backends, pinned to exact source commits.
