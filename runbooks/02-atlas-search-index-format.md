# Incident 02: Atlas Search index creation failed with MISSING_ATTRIBUTE

## Issue
Creating the vector and text search indexes via Atlas CLI failed with the
following error:

    HTTP 400 Bad Request (Error code: "MISSING_ATTRIBUTE")
    Detail: The required attribute [fields] was not specified.

The index definition JSON files appeared to be well-formed and the `fields`
attribute was present in the file. Atlas was rejecting the submission anyway.

## Root Cause
The Atlas CLI passes the index definition JSON directly to the Atlas
Search REST API. The CLI version in use (v1.49) required the `fields`
array at the **top level** of the document, but the carried-forward
definitions had `fields` nested inside a `definition` wrapper:

    // What the CLI rejected (wrapped):
    {
      "name": "plot_vector_index",
      "type": "vectorSearch",
      "definition": {
        "fields": [ ... ]
      }
    }

    // What the CLI accepted (flat):
    {
      "name": "plot_vector_index",
      "type": "vectorSearch",
      "fields": [ ... ]
    }

The text index definition had a different issue. It was structured correctly
with `mappings.fields`, but the top-level `type` field was missing entirely.
Atlas requires `"type": "search"` for an Atlas Search (text) index, just as
`"type": "vectorSearch"` is required for a vector search index.

## Troubleshooting Steps
1. Read the error message carefully — it specifically called out `[fields]`
   as the missing attribute, but the file did contain a `fields` array.
2. Recognized that "missing at the level the API expects" is different from
   "missing in the file". Checked the Atlas CLI documentation link from the
   `--help` output (`atlas clusters search indexes create --help`) which
   pointed to current schema documentation for vector and search indexes.
3. Compared file structure against the documented schema. Found the vector
   index file had an unnecessary `definition` wrapper.
4. After fixing the vector index, preemptively inspected the text index
   file. Found it was missing the `type` field.

## Resolution
1. Flattened `index_definitions/vector_index.json` by removing the
   `definition` wrapper, leaving `fields` at the top level.
2. Added `"type": "search"` to `index_definitions/text_index.json`.
3. Re-ran the index creation tasks (`./ops.sh` options 3 and 4). Both
   indexes were created successfully and reached `STEADY` status within
   a few minutes.

## Prevention
- Treat index definition files as living artifacts, not carried-forward
  artifacts. Atlas Search schemas have evolved across CLI versions; a
  definition that worked previously is not guaranteed to work today.
- When picking up index definitions from older work, sanity-check them
  against the current Atlas Search and Vector Search index documentation
  before submitting.
- When the Atlas CLI rejects a submission with `MISSING_ATTRIBUTE`, the
  attribute may be present in the file but at the wrong nesting level.
  Compare the file structure to the current schema rather than assuming
  the attribute is missing.

---

(Some identifiers in error excerpts have been redacted; structure preserved.)