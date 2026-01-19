# LaTeX Modular Content Benchmark

This repository contains materials for answering a question about the performance of a modular approach in LaTeX on StackExchange.

**Full research text and conclusions in Russian:** [Note.md](Note.md)

**Full research text and conclusions in English:** [Note_eng.md](Note_eng.md)

**Original question:** [Does catchfilebetweentags significantly slow down LaTeX compilation?](https://tex.stackexchange.com/questions/758113/does-catchfilebetweentags-significantly-slow-down-latex-compilation)

---

### Brief Description

Comparison of compilation time when using:
- The `catchfilebetweentags` package with `\ExecuteMetaData`
- An alternative approach based on `\@namedef` and `\@nameuse`

Results show significant slowdown when using `catchfilebetweentags` in documents with many blocks ($>100$), while the alternative approach demonstrates performance close to a "flat" document.

---

### Structure

- `Note.md` -- full research text in Russian
- `Note_eng.md` -- full research text in English
- Scripts for generating test documents and performance measurements
- Measurement results and graphs in corresponding directories

---

*To reproduce the results, follow the instructions in `Note.md` or `Note_eng.md`.*