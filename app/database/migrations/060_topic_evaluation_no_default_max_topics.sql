-- 060: drop the global default's settings.max_topics.
--
-- Topic extraction no longer caps the topic count unless a template's own
-- evaluation_config explicitly sets settings.max_topics. Templates enabling
-- topic evaluation copy this global default row (see 044's
-- initialize_evaluation_config_query), so the cap must be removed here too,
-- not just in app code, for "unlimited by default" to actually apply to
-- newly-enabled templates.

UPDATE evaluation_config
SET configuration = configuration #- '{settings,max_topics}'
WHERE template_id IS NULL
  AND evaluation_type = 'TOPIC';
