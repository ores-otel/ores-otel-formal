module telemetry_pipeline {
  var ingested: int
  var redacted: int
  var exported: int
  var secret_raw: bool

  action init = {
    ingested' = 0
    redacted' = 0
    exported' = 0
    secret_raw' = false
  }

  action step = {
    any {
      all {
        ingested' = ingested + 1,
        redacted' = redacted,
        exported' = exported,
        secret_raw' = true,
      },
      all {
        secret_raw,
        redacted' = redacted + 1,
        secret_raw' = false,
        ingested' = ingested,
        exported' = exported,
      },
      all {
        redacted > exported,
        exported' = exported + 1,
        ingested' = ingested,
        redacted' = redacted,
        secret_raw' = secret_raw,
      },
    }
  }

  val no_secret_export = (exported <= redacted) and (not secret_raw or ingested > exported)
}
