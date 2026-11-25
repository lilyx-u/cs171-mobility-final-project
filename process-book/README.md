# Process book

**The process book to submit is [`CS1710_Process_Book_Final.pdf`](CS1710_Process_Book_Final.pdf).**

It is assembled from two things:

1. `base/GoogleDoc_export_through_Milestone11.pdf`: the export of the team's
   Google Doc (link on page 1 of the PDF), which holds every milestone through
   Milestone 11.
2. `FINAL.md`: the final section (what changed after Prototype V3, the final
   design, the website link), written here as Markdown and appended by a script.

## Before submitting

`FINAL.md` has two `TODO` lines near the top, for the **website URL** and the
**screencast**. Fill them in, then rebuild:

```
python process-book/build_process_book.py
```

That rewrites `CS1710_Process_Book_Final.pdf`: all the Google Doc pages, then the
final section.

If the Google Doc changes, export it to PDF again and either replace the file in
`base/` or pass the new export with `--base "new export.pdf"`. The Markdown also
pastes cleanly into Google Docs (headings, bullets, bold, tables, image
references) if you would rather keep everything in the Doc; `--no-base` builds
just the new pages.

## Files

| Path | What |
|---|---|
| `CS1710_Process_Book_Final.pdf` | The finished process book |
| `FINAL.md` | The final section (source) |
| `base/GoogleDoc_export_through_Milestone11.pdf` | Google Doc export that the final section is appended to |
| `PROTOTYPE_V1.md`, `PROTOTYPE_V3.md` | Markdown sources of the Milestone 8 and Milestone 11 sections, already in the Google Doc |
| `MILESTONE10.md`, `MILESTONE11.md` | Change lists for Prototype V2 and V3 |
| `build_process_book.py` | Markdown to PDF, appended to the base PDF |
| `images/` | Website screenshots used in the book (`final_*.jpg` are the final site) |
| `drafts/` | The three design-draft sketches (SVG) and the script that generated them |

Building needs Python with `pypdf`, `reportlab` and `svglib`:

```
pip install pypdf reportlab svglib
```
