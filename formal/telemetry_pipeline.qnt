module telemetry_pipeline {
  type RedactionPhase = NoRawSecret | RawSecretPending

  pure val capacity = 3

  var ingested: int
  var redacted: int
  var exported: int
  var redaction_phase: RedactionPhase

  action init = all {
    ingested' = 0,
    redacted' = 0,
    exported' = 0,
    redaction_phase' = NoRawSecret,
  }

  action step = {
    any {
      all {
        redaction_phase == NoRawSecret,
        ingested < capacity,
        ingested' = ingested + 1,
        redacted' = redacted,
        exported' = exported,
        redaction_phase' = RawSecretPending,
      },
      all {
        redaction_phase == RawSecretPending,
        redacted' = redacted + 1,
        redaction_phase' = NoRawSecret,
        ingested' = ingested,
        exported' = exported,
      },
      all {
        redacted > exported,
        exported' = exported + 1,
        ingested' = ingested,
        redacted' = redacted,
        redaction_phase' = redaction_phase,
      },
      all {
        ingested' = ingested,
        redacted' = redacted,
        exported' = exported,
        redaction_phase' = redaction_phase,
      },
    }
  }

  val no_secret_export = exported <= redacted

  val pipeline_accounting = all {
    0 <= exported,
    exported <= redacted,
    redacted <= ingested,
    ingested <= capacity,
  }

  val redaction_phase_consistent = or {
    all {
      redaction_phase == NoRawSecret,
      ingested == redacted,
    },
    all {
      redaction_phase == RawSecretPending,
      ingested == redacted + 1,
    },
  }
}
