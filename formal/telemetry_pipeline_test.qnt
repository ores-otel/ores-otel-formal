module telemetry_pipeline_test {
  import telemetry_pipeline.* from "./telemetry_pipeline"

  run rawSecretCannotExportTest =
    init
      .then(ingest)
      .expect(all {
        raw_secret_pending_reached,
        ingested == 1,
        redacted == 0,
        exported == 0,
        no_secret_export,
        pipeline_accounting,
        redaction_phase_consistent,
      })
      .then(export_one)
      .fail()

  run redactionEnablesExportTest =
    init
      .then(ingest)
      .then(redact)
      .expect(all {
        redaction_reached,
        ingested == 1,
        redacted == 1,
        exported == 0,
        no_secret_export,
        pipeline_accounting,
        redaction_phase_consistent,
      })
      .then(export_one)
      .expect(all {
        export_reached,
        ingested == 1,
        redacted == 1,
        exported == 1,
        no_secret_export,
        pipeline_accounting,
        redaction_phase_consistent,
      })

  run capacityIsHardBoundTest =
    init
      .then(ingest)
      .then(redact)
      .then(ingest)
      .then(redact)
      .then(ingest)
      .expect(all {
        capacity_reached,
        ingested == capacity,
        redaction_phase == RawSecretPending,
        pipeline_accounting,
        redaction_phase_consistent,
      })
      .then(redact)
      .then(ingest)
      .fail()

  run exportCannotOutrunRedactionTest =
    init
      .then(ingest)
      .then(redact)
      .then(export_one)
      .then(export_one)
      .fail()
}
