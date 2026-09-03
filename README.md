# ores-otel-formal

Product-owned formal methods for `ores-otel`. The reusable runner, batch
protocol (`fmctl.adapter.v1`), and streaming protocol (`fm.adapter.stream.v1`)
live in [ORESoftware/formal-methods.rs](https://github.com/ORESoftware/formal-methods.rs).
This repository keeps the Quint model and adapter slots beside `ores-otel` code.

Model: `telemetry_pipeline` (`formal/telemetry_pipeline.qnt`). The finite state
machine distinguishes `NoRawSecret` from `RawSecretPending` and checks all of:

- `no_secret_export`
- `pipeline_accounting`
- `redaction_phase_consistent`

## Commands

From a machine that has the shared runner cloned at
`~/codes/oresoftware/formal-methods.rs`:

```bash
python3 scripts/validate_manifest.py
scripts/run-fmctl.sh validate
scripts/run-fmctl.sh check
scripts/run-fmctl.sh simulate
scripts/run-fmctl.sh verify
```

`formal/echo.py` is only a protocol-envelope fixture. It deliberately reports a
conformance mismatch for every trace because it cannot execute the product or
compare observable state. Accordingly, every language adapter remains `planned`
until a real product runtime adapter lands; `fmctl replay` fails closed today.

Exercise that fail-closed fixture directly with a fixture request:

```bash
printf '%s' '{"adapter":"rust","traces":["formal/trace-0.itf.json"]}' \
  | python3 formal/echo.py
```

## Linear

Parent platform issue: [DEN-565](https://linear.app/denman/issue/DEN-565).
Shared runner: [DEN-580](https://linear.app/denman/issue/DEN-580).
