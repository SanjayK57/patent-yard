-- One row per patent application worldwide: its representative publication (the grant if there is one), English title
-- (else the original), a short English abstract, first owner and inventor, and up to four classification codes.
SELECT
  application_number AS app,
  ANY_VALUE(country_code) AS cc,
  ANY_VALUE(family_id) AS fam,
  ARRAY_AGG(STRUCT(publication_number AS pn, kind_code AS kind) ORDER BY grant_date > 0 DESC, publication_date DESC LIMIT 1)[OFFSET(0)].*,
  MAX(IF(filing_date > 0, filing_date, NULL)) AS f,
  MIN(IF(publication_date > 0, publication_date, NULL)) AS p,
  MAX(IF(grant_date > 0, grant_date, NULL)) AS g,
  MIN(IF(priority_date > 0, priority_date, NULL)) AS pr,
  ARRAY_AGG((SELECT t.text FROM UNNEST(title_localized) t WHERE t.text != '' ORDER BY t.language = 'en' DESC LIMIT 1) IGNORE NULLS LIMIT 1)[SAFE_OFFSET(0)] AS t,
  ARRAY_AGG((SELECT t.language FROM UNNEST(title_localized) t WHERE t.text != '' ORDER BY t.language = 'en' DESC LIMIT 1) IGNORE NULLS LIMIT 1)[SAFE_OFFSET(0)] AS tl,
  ARRAY_AGG((SELECT SUBSTR(a.text, 1, 320) FROM UNNEST(abstract_localized) a WHERE a.language = 'en' AND a.text != '' LIMIT 1) IGNORE NULLS LIMIT 1)[SAFE_OFFSET(0)] AS ab,
  ARRAY_AGG((SELECT h.name FROM UNNEST(assignee_harmonized) h LIMIT 1) IGNORE NULLS LIMIT 1)[SAFE_OFFSET(0)] AS a,
  ARRAY_AGG((SELECT h.name FROM UNNEST(inventor_harmonized) h LIMIT 1) IGNORE NULLS LIMIT 1)[SAFE_OFFSET(0)] AS i,
  ARRAY_AGG((SELECT ARRAY_TO_STRING(ARRAY(SELECT c.code FROM UNNEST(cpc) c ORDER BY c.first DESC, c.inventive DESC LIMIT 4), ' ')) IGNORE NULLS LIMIT 1)[SAFE_OFFSET(0)] AS cpc
FROM `patents-public-data.patents.publications`
WHERE application_number != '' AND country_code != 'WO'
GROUP BY application_number
