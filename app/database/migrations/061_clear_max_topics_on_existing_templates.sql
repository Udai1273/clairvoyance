-- 061: clear settings.max_topics on existing per-template TOPIC configs.
--
-- 060 removed the cap from the global default row, but templates that
-- enabled topic evaluation before that only copied the old default
-- (max_topics: 3) into their own row at creation time (044's
-- initialize_evaluation_config_query) and never re-read the global row
-- afterward. Clearing it here makes "unlimited unless specified" apply
-- retroactively, not just to templates enabled from now on. Uncapping is
-- non-destructive (extraction only returns more topics, never fewer); an
-- explicit cap can still be set per template via the topic-config API.

UPDATE evaluation_config
SET configuration = configuration #- '{settings,max_topics}'
WHERE template_id IS NOT NULL
  AND evaluation_type = 'TOPIC';
