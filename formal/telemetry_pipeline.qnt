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

  // Keep the transition relation factored into named actions so deterministic
  // proof traces can exercise the same operations used by the model checker.
  action ingest = all {
    redaction_phase == NoRawSecret,
    ingested < capacity,
    ingested' = ingested + 1,
    redacted' = redacted,
    exported' = exported,
    redaction_phase' = RawSecretPending,
  }

  action redact = all {
    redaction_phase == RawSecretPending,
    redacted' = redacted + 1,
    redaction_phase' = NoRawSecret,
    ingested' = ingested,
    exported' = exported,
  }

  action export_one = all {
    redacted > exported,
    exported' = exported + 1,
    ingested' = ingested,
    redacted' = redacted,
    redaction_phase' = redaction_phase,
  }

  action idle = all {
    ingested' = ingested,
    redacted' = redacted,
    exported' = exported,
    redaction_phase' = redaction_phase,
  }

  action step = any {
    ingest,
    redact,
    export_one,
    idle,
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

  // Required simulation witnesses keep the safety proof non-vacuous. CI must
  // demonstrate states with an unredacted item, completed redaction, export,
  // and a full bounded ingest queue instead of proving only the initial state.
  val raw_secret_pending_reached =
    redaction_phase == RawSecretPending

  val redaction_reached =
    redacted > 0

  val export_reached =
    exported > 0

  val capacity_reached =
    ingested == capacity
}
