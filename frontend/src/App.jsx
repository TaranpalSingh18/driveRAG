import { useEffect, useState } from "react";

function formatJson(data) {
  return JSON.stringify(data, null, 2);
}

function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [k, setK] = useState(5);
  const [query, setQuery] = useState("");

  const [files, setFiles] = useState([]);
  const [stats, setStats] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [finalAnswer, setFinalAnswer] = useState("");

  const [loading, setLoading] = useState({
    files: false,
    index: false,
    search: false,
    stats: false
  });

  const [messages, setMessages] = useState([]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("auth") === "success") {
      pushMessage("success", "Login successful", "You are now connected to your Google Drive.");
      window.history.replaceState({}, document.title, window.location.pathname);
    }
    getAuthStatus();
  }, []);

  function pushMessage(type, title, details) {
    setMessages((prev) => [
      { id: crypto.randomUUID(), type, title, details, time: new Date().toLocaleTimeString() },
      ...prev
    ]);
  }

  async function request(path, options = {}) {
    const res = await fetch(`/api${path}`, {
      ...options,
      credentials: "include"
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const errorText = data?.detail || data?.error || "Request failed";
      throw new Error(errorText);
    }
    return data;
  }

  async function getAuthStatus() {
    try {
      const data = await request("/auth/status");
      setAuthenticated(Boolean(data.authenticated));
      if (!data.authenticated) {
        pushMessage("info", "Not logged in", "Click Login with Google to connect your Drive.");
      }
    } catch (err) {
      pushMessage("error", "Auth check failed", err.message);
    }
  }

  function openLogin() {
    window.location.href = "/api/auth/login";
  }

  async function logout() {
    try {
      await request("/auth/logout", { method: "POST" });
      setAuthenticated(false);
      setFiles([]);
      setSearchResults([]);
      pushMessage("info", "Logged out", "Session cleared.");
    } catch (err) {
      pushMessage("error", "Logout failed", err.message);
    }
  }

  async function getFiles() {
    if (!authenticated) {
      pushMessage("error", "Not logged in", "Please login first.");
      return;
    }
    setLoading((s) => ({ ...s, files: true }));
    try {
      const data = await request("/drive/files");
      const list = data.files || [];
      setFiles(list);
      pushMessage("success", "Fetched files", `${list.length} file records received from Drive.`);
    } catch (err) {
      pushMessage("error", "Fetch files failed", err.message);
    } finally {
      setLoading((s) => ({ ...s, files: false }));
    }
  }

  async function runIndex() {
    if (!authenticated) {
      pushMessage("error", "Not logged in", "Please login first.");
      return;
    }
    setLoading((s) => ({ ...s, index: true }));
    try {
      const data = await request("/drive/index", {
        method: "POST"
      });
      pushMessage(
        "success",
        "Index completed",
        `Processed ${data.files_processed ?? 0} files, created ${data.chunks_created ?? 0} chunks.`
      );
      await getStats();
    } catch (err) {
      pushMessage("error", "Index failed", err.message);
    } finally {
      setLoading((s) => ({ ...s, index: false }));
    }
  }

  async function runSearch() {
    if (!authenticated) {
      pushMessage("error", "Not logged in", "Please login first.");
      return;
    }
    if (!query.trim()) {
      pushMessage("error", "Query missing", "Enter a question to search your Drive index.");
      return;
    }
    setLoading((s) => ({ ...s, search: true }));
    try {
      const data = await request(`/rag/ask?query=${encodeURIComponent(query.trim())}&k=${k}`, { method: "POST" });
      setSearchResults(data.question_answers || []);
      setFinalAnswer(data.final_answer || "");
      pushMessage("success", "Answer ready", `${(data.question_answers || []).length} sub-question answers generated.`);
    } catch (err) {
      pushMessage("error", "Search failed", err.message);
    } finally {
      setLoading((s) => ({ ...s, search: false }));
    }
  }

  async function getStats() {
    setLoading((s) => ({ ...s, stats: true }));
    try {
      const data = await request("/rag/stats");
      setStats(data);
      pushMessage("info", "DB stats updated", "Vector DB status refreshed.");
    } catch (err) {
      pushMessage("error", "Stats failed", err.message);
    } finally {
      setLoading((s) => ({ ...s, stats: false }));
    }
  }

  return (
    <div className="page-shell">
      <header className="hero">
        <p className="eyebrow">Drive RAG Control Panel</p>
        <h1>Index everything from Drive, then ask in one flow.</h1>
        <p>
          Login -&gt; File scan -&gt; Vector indexing -&gt; Ask question. No token copy-paste needed.
        </p>
        <p>
          {authenticated
            ? "Status: Connected to Google Drive"
            : "Status: Not connected. Login once and this app will handle session automatically."}
        </p>
      </header>

      <section className="panel config-panel">
        <div className="actions-row">
          {!authenticated ? (
            <button onClick={openLogin}>1. Login With Google</button>
          ) : (
            <button onClick={logout}>Logout</button>
          )}
          <button onClick={getFiles} disabled={loading.files || !authenticated}>
            2. Fetch Files {loading.files ? "..." : ""}
          </button>
          <button onClick={runIndex} disabled={loading.index || !authenticated}>
            3. Build Index {loading.index ? "..." : ""}
          </button>
          <button onClick={getStats} disabled={loading.stats}>
            Refresh Stats {loading.stats ? "..." : ""}
          </button>
        </div>
      </section>

      <section className="grid-two">
        <article className="panel">
          <h2>Drive Files</h2>
          <p className="sub">Preview file IDs and names from your connected Drive scope.</p>
          <div className="list-scroll">
            {files.length === 0 && <p className="muted">No files loaded yet.</p>}
            {files.map((file) => (
              <div className="list-item" key={file.id}>
                <div>
                  <p className="item-title">{file.name || "Untitled"}</p>
                  <p className="item-meta">{file.mimeType}</p>
                </div>
                <code>{file.id}</code>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <h2>Vector DB Stats</h2>
          <p className="sub">Confirm index health and available search components.</p>
          <pre className="code-block">{stats ? formatJson(stats) : "Run Refresh Stats to load status."}</pre>
        </article>
      </section>

      <section className="panel">
        <h2>Ask Anything</h2>
        <p className="sub">Query is split into sub-questions, answered with BM25 + vector retrieval, then merged.</p>
        <div className="search-row">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask anything from your Drive documents"
          />
          <label className="k-input">
            Top K
            <input
              type="number"
              min={1}
              max={20}
              value={k}
              onChange={(e) => setK(Number(e.target.value) || 5)}
            />
          </label>
          <button onClick={runSearch} disabled={loading.search || !authenticated}>
            Search {loading.search ? "..." : ""}
          </button>
        </div>

        <div className="result-stack">
          {!finalAnswer && <p className="muted">No answer yet.</p>}

          {finalAnswer && (
            <article className="result-card">
              <div className="result-head">
                <span>Final Answer</span>
              </div>
              <p>{finalAnswer}</p>
            </article>
          )}

          {searchResults.map((result, idx) => (
            <article className="result-card" key={`${idx}-${result.score}`}>
              <div className="result-head">
                <span>Question {idx + 1}</span>
              </div>
              <p><strong>{result.question}</strong></p>
              <p>{result.answer}</p>
              <pre className="result-source">{formatJson((result.chunks || []).map((c) => c.source || {}))}</pre>
            </article>
          ))}
        </div>
      </section>

      <section className="panel log-panel">
        <h2>Activity Log</h2>
        <div className="log-list">
          {messages.length === 0 && <p className="muted">No actions yet.</p>}
          {messages.map((msg) => (
            <div key={msg.id} className={`log-item ${msg.type}`}>
              <div>
                <strong>{msg.title}</strong>
                <p>{msg.details}</p>
              </div>
              <span>{msg.time}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default App;
