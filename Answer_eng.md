#### Short Answer
1. **For small projects (up to ~50 blocks),** the difference in compilation time between different approaches is negligible (fractions of a second). In this case, the choice of method can be based on convenience and personal preference.

2. **For medium and large projects (from 100 blocks and more),** using the `catchfilebetweentags` package leads to a noticeable increase in compilation time, especially if the text fragments contain multi-line content (`modular_inner`), rather than just macro calls (`\lipsum`). This is critical for iterative compilation when `pdflatex` is run multiple times.

3. **The alternative solution** based on `\@namedef` and `\@nameuse` demonstrates performance comparable to "flat" (`flat_inner`) text inclusion and is a more predictable approach. It is well-suited for the tasks described in the original question.

#### Briefly About the Measurement Context
 - **Baseline:** The document of type `flat_inner` was taken as the reference point, where all text and images are included directly in the main `.tex` file. This allows measuring the "overhead of modularity."
 
 - **Environment:** Testing was performed on Arch Linux with `pdflatex` from TeX Live 2024 (TeX 3.141592653-2.6-1.40.26).

 - **Time Measurement Methodology:**
   
   - Using the standard `time` command;
   - Using the `l3benchmark` package.

  For more details, see the section ["How to measure time"](Note_eng.md#how-to-measure-time) in the full [note](Note_eng.md).

#### Types of Compared Documents

Six different types of documents were measured:

1. `flat` -- the closest analogue to the example given in the question, but without splitting into several `.tex` files.
2. `flat_inner` -- an analogue of flat, but the text is included directly, not via `\lipsum`.
3. `modular` -- the closest analogue to the example given in the question.
4. `modular_inner` -- an analogue of modular, but the text is included directly, not via `\lipsum` (most closely resembles the real use case from the question).
5. `modular_inner_last` -- an analogue of `modular_inner`, but always calling the last tag defined in `des.tex` and `data.tex`.
6. `macrodef` -- the solution using `\@namedef` and `\@nameuse`.

For more details, see the section ["What to measure"](Note_eng.md#what-to-measure).

#### Key Results Visualized 

Graphs for $N \le 200$:

![alt text](plots_200/en_2_mean_time_comparison.png) 
![alt text](plots_200/en_3_mean_benchmark_comparison.png)

![alt text](plots_200/en_4_difference_modular_inner_vs_flat_inner.png)


Results for $200 < N < 2000$ are available in the repository. For more details on construction and description, see the section ["Main results"](Note_eng.md#main-results).

#### Briefly About the Alternative Solution

In the `des.tex` files, wrap fragments in `\@namedef{desDes<N>}`:
```tex
\@namedef{desDes1}{%
Text ...
...
}

\@namedef{desDes2}{%
Text ...
...
}
...
```
Similarly, in `data.tex`:
```tex
\@namedef{dataData1}{%
Data ...
...
}
...
```
And in the main document `main.tex`:
```tex
\makeatletter
\newcommand{\merge}[4]{\par\textbf{#1}\par\fig{#2}\@nameuse{#3}\par\@nameuse{#4}\par}
\makeatother
...
\makeatletter
\input{des.tex}
\input{data.tex}
\makeatother
...
\merge{Block 1}{images/test-image-1.png}{desDes1}{dataData1}
\merge{Block 2}{images/test-image-2.png}{desDes2}{dataData2}
```
This solution provides performance close to "flat" (`flat_inner`) text inclusion.

![alt text](plots/en_4_difference_macrodef_vs_flat_inner.png)

For more details, see the section ["Alternative solution"](Note_eng.md#alternative-solution).

**Note:** Your question is quite extensive and deserves more of a small note than a brief answer, so I have detailed my reasoning with possible modifications and experiments in my [GitHub repository](https://github.com/DacrydiumGracile/latex-catchfilebetweentags-benchmark). There you will also find the full version of this [note](Note_eng.md), scripts to reproduce the results, and additional materials. Since my English level leaves much to be desired, the [original](Note.md) in Russian is also available in the repository. If you have any questions about the methodology, scripts, or require additional measurements, please contact me in the comments.