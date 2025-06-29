"use client";
import React, { useState, useRef } from "react";

interface SourceTeamMap {
  [key: string]: string;
}

export default function Home() {
  const [files, setFiles] = useState<File[]>([]);
  const [urlsRaw, setUrlsRaw] = useState("");
  const [urls, setUrls] = useState<string[]>([]);
  const [maxPages, setMaxPages] = useState(10);
  const [output, setOutput] = useState<string | null>(null);
  const [outputJson, setOutputJson] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  // Handle file input and initialize team IDs
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const filesArr = Array.from(e.target.files);
      setFiles(filesArr);
    } else {
      setFiles([]);
    }
  };

  // Handle blog URLs input (raw textarea value and parsed URLs)
  const handleUrlsChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setUrlsRaw(value);
    const urlArr = value.split("\n").map(u => u.trim()).filter(Boolean);
    setUrls(urlArr);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setOutput(null);
    setOutputJson(null);
    setLoading(true);
    setProgress(0);
    try {
      // Assign team IDs automatically
      const sourceTeamMap: { [key: string]: string } = {};
      files.forEach((file, idx) => {
        sourceTeamMap[file.name] = `team_${idx + 1}`;
      });
      urls.forEach((url, idx) => {
        sourceTeamMap[url] = `team_${files.length + idx + 1}`;
      });
      const formData = new FormData();
      files.forEach((file) => {
        formData.append("files", file);
      });
      formData.append("urls", urls.join("\n"));
      formData.append("max_pages", String(maxPages));
      formData.append("source_team_map", JSON.stringify(sourceTeamMap));
      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${backendUrl}/scrape-all`, true);
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          setProgress(Math.round((event.loaded / event.total) * 100));
        }
      };
      xhr.onreadystatechange = () => {
        if (xhr.readyState === 4) {
          setLoading(false);
          if (xhr.status === 200) {
            setOutput(xhr.responseText);
            try {
              setOutputJson(JSON.parse(xhr.responseText));
            } catch {
              setOutputJson(null);
            }
          } else {
            setError("Failed to fetch output");
          }
        }
      };
      xhr.send(formData);
    } catch (err: any) {
      setError(err.message || "Unknown error");
      setLoading(false);
    }
  };

  const handleDownloadJson = () => {
    if (!output) return;
    const blob = new Blob([output], { type: "application/json" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "knowledgebase_output.json";
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const handleDownloadMarkdown = () => {
    if (!outputJson || !outputJson.items) return;
    const mdContent = outputJson.items.map((item: any) => `# ${item.title}\n\n${item.content}`).join("\n\n---\n\n");
    const blob = new Blob([mdContent], { type: "text/markdown" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "knowledgebase_output.md";
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(120deg, #f0f4ff 0%, #e0e7ff 100%)",
      fontFamily: "'Inter', 'Segoe UI', Arial, sans-serif",
      padding: 0,
      margin: 0
    }}>
      <header style={{
        background: "linear-gradient(90deg, #6366f1 0%, #60a5fa 100%)",
        color: "#fff",
        padding: "2rem 0 1rem 0",
        textAlign: "center",
        letterSpacing: 1,
        fontWeight: 700,
        fontSize: 32,
        boxShadow: "0 2px 8px rgba(99,102,241,0.08)"
      }}>
        Knowledgebase Import Tool
        <div style={{ fontWeight: 400, fontSize: 18, marginTop: 8, opacity: 0.9 }}>
          Import technical knowledge from PDFs and blogs and download as JSON or Markdown.
        </div>
      </header>
      <main style={{
        maxWidth: 700,
        margin: "2rem auto",
        padding: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center"
      }}>
        <div style={{
          background: "#fff",
          borderRadius: 16,
          boxShadow: "0 4px 24px rgba(99,102,241,0.10)",
          padding: 32,
          width: "100%",
          maxWidth: 600,
          marginBottom: 32
        }}>
          <form onSubmit={handleSubmit} style={{ marginBottom: 24 }}>
            <div style={{ marginBottom: 24 }}>
              <label style={{ fontWeight: 600, color: "#6366f1" }}>Upload PDF(s):</label>
              <input
                type="file"
                accept="application/pdf"
                multiple
                onChange={handleFileChange}
                ref={fileInputRef}
                style={{ display: "block", marginTop: 8 }}
              />
              {files.length > 0 && (
                <table style={{ width: "100%", marginTop: 12, fontSize: 15, borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ background: "#f3f4f6" }}>
                      <th align="left" style={{ padding: 6, borderRadius: 6 }}>File</th>
                    </tr>
                  </thead>
                  <tbody>
                    {files.map((file) => (
                      <tr key={file.name} style={{ borderBottom: "1px solid #e5e7eb" }}>
                        <td style={{ padding: 6 }}>{file.name}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
            <div style={{ marginBottom: 24 }}>
              <label style={{ fontWeight: 600, color: "#6366f1" }}>Blog URL(s):</label>
              <textarea
                placeholder="Enter one blog URL per line"
                value={urlsRaw}
                onChange={handleUrlsChange}
                style={{ width: "100%", padding: 10, minHeight: 80, marginTop: 8, border: "1px solid #c7d2fe", borderRadius: 6, fontSize: 15 }}
              />
              {urls.length > 0 && (
                <table style={{ width: "100%", marginTop: 12, fontSize: 15, borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ background: "#f3f4f6" }}>
                      <th align="left" style={{ padding: 6, borderRadius: 6 }}>URL</th>
                    </tr>
                  </thead>
                  <tbody>
                    {urls.map((url) => (
                      <tr key={url} style={{ borderBottom: "1px solid #e5e7eb" }}>
                        <td style={{ padding: 6, wordBreak: "break-all" }}>{url}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
            <div style={{ marginBottom: 24, display: "flex", alignItems: "center" }}>
              <label style={{ fontWeight: 600, color: "#6366f1" }}>Max Pages to Crawl (per blog):</label>
              <input
                type="number"
                min={1}
                max={100}
                value={maxPages}
                onChange={e => setMaxPages(Number(e.target.value))}
                style={{ width: 80, marginLeft: 12, border: "1px solid #c7d2fe", borderRadius: 4, padding: 4, fontSize: 15 }}
              />
            </div>
            <button type="submit" disabled={loading} style={{
              marginTop: 12,
              padding: "0.7rem 2.2rem",
              background: loading ? "#a5b4fc" : "#6366f1",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              fontWeight: 600,
              fontSize: 18,
              boxShadow: "0 2px 8px rgba(99,102,241,0.08)",
              cursor: loading ? "not-allowed" : "pointer",
              transition: "background 0.2s"
            }}>
              {loading ? "Processing..." : "Import"}
            </button>
            {loading && (
              <div style={{ marginTop: 24 }}>
                <div style={{ height: 10, background: "#e0e7ff", borderRadius: 5, overflow: "hidden" }}>
                  <div style={{ width: `${progress}%`, height: 10, background: "#6366f1", transition: "width 0.2s" }} />
                </div>
                <div style={{ marginTop: 8, fontSize: 14, color: "#6366f1" }}>
                  Uploading... {progress}%
                </div>
                <div style={{ marginTop: 4, fontSize: 13, color: "#64748b" }}>
                  Processing may take a few minutes depending on the number of sources and pages.
                </div>
              </div>
            )}
          </form>
          {error && <div style={{ color: "#dc2626", marginBottom: 16, fontWeight: 500 }}>{error}</div>}
          {output && (
            <div style={{ marginTop: 32 }}>
              <h3 style={{ color: "#6366f1", fontWeight: 700, fontSize: 22, marginBottom: 12 }}>Output JSON</h3>
              <pre style={{ background: "#f4f4f4", padding: 18, borderRadius: 10, maxHeight: 400, overflow: "auto", fontSize: 15 }}>{output}</pre>
              <div style={{ display: "flex", gap: 16, marginTop: 16 }}>
                <button onClick={handleDownloadJson} style={{ padding: "0.6rem 1.5rem", background: "#60a5fa", color: "#fff", border: "none", borderRadius: 7, fontWeight: 600, fontSize: 16, cursor: "pointer" }}>
                  Download JSON
                </button>
                <button onClick={handleDownloadMarkdown} style={{ padding: "0.6rem 1.5rem", background: "#6366f1", color: "#fff", border: "none", borderRadius: 7, fontWeight: 600, fontSize: 16, cursor: "pointer" }}>
                  Download Markdown (.md)
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
      <footer style={{ textAlign: "center", color: "#64748b", fontSize: 15, margin: "2rem 0 1rem 0" }}>
        &copy; {new Date().getFullYear()} Knowledgebase Import Tool. Built with Next.js & FastAPI.
      </footer>
    </div>
  );
}
