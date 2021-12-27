issues to fix

- fix mistune breaking multiline list entries

```
-<li>Using virtual machines or operating system containers to manage the runtime
-(except as described in <a href="CommandLineTool.html#DockerRequirement">DockerRequirement</a>).</li>
+<li>Using virtual machines or operating system containers to manage the runtime</li>
+</ul>
+<p>(except as described in <a href="CommandLineTool.html#DockerRequirement">DockerRequirement</a>).</p>
+<ul>
 <li>Using remote or distributed file systems to manage input and output files.</li>
 <li>Transforming file paths.</li>
-<li>Determining if a process has previously been executed, skipping it and
-reusing previous results.</li>
+<li>Determining if a process has previously been executed, skipping it and</li>
+</ul>
+<p>reusing previous results.</p>
+<ul>
```

- fix remaining overquoting: `"` → `&quot;`

new tests

- mistune escaping raw HTML test (table of contents token, for example)
- mistune plain url hyperlink test
- mistune heading hyperlink target test (header→heading rename)
- mistune table test (when the table plugin isn't loaded)




