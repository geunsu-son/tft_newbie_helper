import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function App() {
  const [units, setUnits] = useState([]);
  const [selected, setSelected] = useState([]);
  const [stars, setStars] = useState({});
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [patch, setPatch] = useState(null);
  const [error, setError] = useState("");
  const [meta, setMeta] = useState({});

  useEffect(() => {
    Promise.all([fetch(`${API}/units`).then((r) => r.json()), fetch(`${API}/health`).then((r) => r.json())])
      .then(([loadedUnits, health]) => { setUnits(loadedUnits); setMeta(health.meta || {}); })
      .catch(() => setError("API에 연결할 수 없습니다. 백엔드를 먼저 실행해 주세요."));
  }, []);

  const filtered = useMemo(
    () => units.filter((unit) => (unit.name_ko || unit.name_en).toLowerCase().includes(query.toLowerCase()))
      .filter((unit) => !selected.includes(unit.unit_id)).slice(0, 20),
    [units, query, selected],
  );

  const recommend = async () => {
    if (selected.length < 2) { setError("유닛을 2개 이상 입력해 주세요."); return; }
    setError("");
    const response = await fetch(`${API}/recommend/units`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ unit_ids: selected }),
    });
    const payload = await response.json();
    if (!response.ok) { setError(payload.detail || "추천에 실패했습니다."); return; }
    setResults(payload.recommendations);
  };

  const loadPatches = async () => {
    const response = await fetch(`${API}/patch-notes`);
    const payload = await response.json();
    setPatch(payload);
  };

  return <main>
    <header>
      <p className="eyebrow">TFT NEWBIE HELPER</p>
      <h1>내 유닛으로 갈 덱 찾기</h1>
      <p>KR 에메랄드+ 데이터로 미리 계산한 후보를 보여드립니다.</p>
    </header>
    {!meta.sample_n && <div className="notice">아직 배치 데이터가 없습니다. 백엔드에서 초기 배치를 실행해 주세요.</div>}
    <section className="panel">
      <h2>보유 유닛 <small>({selected.length}/10 · 2개 이상 필요)</small></h2>
      <div className="selected">{selected.map((id) => <span className="unit-input" key={id}><button onClick={() => { setSelected(selected.filter((x) => x !== id)); setStars(({ [id]: _, ...rest }) => rest); }}>{units.find((u) => u.unit_id === id)?.name_ko || id} ×</button><button className="star" onClick={() => setStars({ ...stars, [id]: (stars[id] || 1) % 3 + 1 })}>{stars[id] || 1}★</button></span>)}</div>
      <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="유닛 검색" />
      {query && <div className="suggestions">{filtered.map((unit) => <button key={unit.unit_id} onClick={() => { setSelected([...selected, unit.unit_id]); setStars({ ...stars, [unit.unit_id]: 1 }); setQuery(""); }}>{unit.name_ko || unit.name_en}</button>)}</div>}
      <button className="primary" onClick={recommend}>추천 보기</button>
      {error && <p className="error">{error}</p>}
    </section>
    <section>
      <div className="section-title"><h2>추천 덱</h2><span>{results.length ? "점수순" : "입력 후 표시됩니다"}</span></div>
      <div className="cards">{results.map((item) => <article className="card" key={item.cluster_id}>
        <h3>{item.deck_name}</h3><strong>{(item.score * 100).toFixed(1)}점</strong>
        <p>평균 등수 {item.avg_placement} · Top4 {(item.top4_rate * 100).toFixed(1)}% · 1등 {(item.win_rate * 100).toFixed(1)}%</p>
        <p>유닛 유사도 {(item.similarity * 100).toFixed(1)}% · 표본 {item.sample_n}</p>
        <p className="next">다음 유닛: {item.next_units.join(", ") || "핵심 유닛을 모두 포함"}</p>
      </article>)}</div>
    </section>
    <section className="panel patch"><div className="section-title"><h2>패치 변경점</h2><button onClick={loadPatches}>공식 노트 불러오기</button></div>
      {patch ? <><p>출처: <a href={patch.source} target="_blank">{patch.source}</a></p>{patch.changes?.map((change, index) => <p key={index}><b>{change.type}</b> — {change.text}</p>)}</> : <p>공식 TFT 패치 노트의 상향·하향 내용을 확인합니다.</p>}
    </section>
    <footer>로컬·내부망 전용 · KR 에메랄드+ 고정 · 평균 등수/Top4/1등은 관측 표본 기준</footer>
    <footer className="riot">TFT 뉴비 헬퍼는 Riot Games의 보증을 받지 않으며 Riot Games 또는 관련 공식 기관의 견해를 반영하지 않습니다.</footer>
  </main>;
}

createRoot(document.getElementById("root")).render(<App />);
