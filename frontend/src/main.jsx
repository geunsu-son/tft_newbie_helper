import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const API = "/api";
const referenceUnitImages = {
  DA_18_Kobuko: "tft18_kobuko.tft_set18.jpg",
  DA_18_Teemo: "tft18_teemo.tft_set18.jpg",
  DA_18_Alune: "tft18_alune.tft_set18.jpg",
  DA_18_ElderDragon: "TheElderDragon.jpg",
};
const referenceUnitAssets = {
  DA_Cinderling18: "tft18_cinderling/skins/base/images/t_18_cinderling_teamplannersplash.png",
  DA_18_Sentry: "tft18_sentry/skins/base/images/t_18_sentry_teamplannersplash.png",
  DA_Gromp18_AP: "tft18_gromp/skins/base/images/t_18_gromp_teamplannersplash.png",
  DA_Murkwolf18: "tft18_murkwolf/skins/base/images/t_18_murkwolf_teamplannersplash.png",
  DA_Scuttlecrab18: "tft18_scuttlecrab/skins/base/images/t_18_scuttlecrab_teamplannersplash.png",
  DA_Krug18: "tft18_krug/skins/base/images/t_18_krug_teamplannersplash.png",
  DA_CrimsonRaptor18: "tft18_raptor/skins/base/images/t_18_crimsonraptor_teamplannersplash.png",
  DA_Brambleback18: "tft18_brambleback/skins/base/images/t_18_brambleback_teamplannersplash.png",
  DA_Sentinel18: "tft18_sentinel/skins/base/images/t_18_sentinel_teamplannersplash.png",
};
const iconUrl = (icon, unitId) => icon?.startsWith("assets/")
  ? `https://raw.communitydragon.org/latest/game/${icon.toLowerCase().replace(/\.tex$/, ".png")}`
  : referenceUnitAssets[unitId]
    ? `https://opgg-web-production.up.railway.app/img/cdragon/game/assets/characters/${referenceUnitAssets[unitId]}`
    : referenceUnitImages[unitId]
    ? `https://c-tft-api.op.gg/img/set/18/tft-champion/tiles/${referenceUnitImages[unitId]}?image=q_auto:good,f_webp,w_92`
    : "";
const renderDeckPreview = (deck, units, items, assignmentSnapshot) => <span className="deck-preview" aria-label="최종 덱 구성">
  <span className="deck-units">{[...(deck.unit_ids || [])].sort((a, b) => { const unitA = units.find((unit) => unit.unit_id === a); const unitB = units.find((unit) => unit.unit_id === b); return (unitA?.cost ?? Infinity) - (unitB?.cost ?? Infinity) || (unitA?.name_ko || a).localeCompare(unitB?.name_ko || b, "ko"); }).map((id) => { const unit = units.find((u) => u.unit_id === id); const snapshot = assignmentSnapshot[deck.cluster_id?.replace(/^lolchess-/, "")]; const assignments = deck.items_by_unit && Object.keys(deck.items_by_unit).length ? deck.items_by_unit : snapshot; const equipped = assignments?.[id] || []; return <span className={`deck-unit cost-${unit?.cost || 1}`} key={id} title={unit?.name_ko || id}>{(unit?.icon || referenceUnitImages[id]) && <img src={iconUrl(unit.icon, id)} alt="" loading="lazy" onError={(e) => { e.currentTarget.hidden = true; }} />}<span className="deck-unit-name">{unit?.name_ko || id}</span>{equipped.length > 0 && <span className="equipped-items" aria-label={`${unit?.name_ko || id} 장착 아이템`}>{equipped.map((name, index) => { const item = items.find((entry) => entry.name_ko === name); return <span className={item?.icon ? "equipped-item" : "equipped-item item-name-fallback"} key={`${name}-${index}`} title={name} aria-label={name}>{item?.icon ? <img src={iconUrl(item.icon)} alt="" loading="lazy" onError={(e) => { e.currentTarget.hidden = true; }} /> : name}</span>; })}</span>}</span>; })}</span>
</span>;
const copyTeamCode = async (deck) => {
  const code = deck.cluster_id?.replace(/^lolchess-/, "");
  if (!code) return;
  try {
    await navigator.clipboard.writeText(code);
  } catch {
    const input = document.createElement("textarea");
    input.value = code;
    document.body.append(input);
    input.select();
    document.execCommand("copy");
    input.remove();
  }
};

function App() {
  const [units, setUnits] = useState([]);
  const [selected, setSelected] = useState([]);
  const [items, setItems] = useState([]);
  const [selectedItems, setSelectedItems] = useState([]);
  const [itemQuery, setItemQuery] = useState("");
  const [itemResults, setItemResults] = useState([]);
  const [stars, setStars] = useState({});
  const [query, setQuery] = useState("");
  const [costFilter, setCostFilter] = useState(0);
  const [traitFilter, setTraitFilter] = useState("");
  const [results, setResults] = useState([]);
  const [patch, setPatch] = useState(null);
  const [error, setError] = useState("");
  const [meta, setMeta] = useState({});
  const [unitItemSnapshot, setUnitItemSnapshot] = useState({});
  const [page, setPage] = useState("unitDecks");

  useEffect(() => {
    Promise.all([fetch(`${API}/units`).then((r) => r.json()), fetch(`${API}/items`).then((r) => r.json()), fetch(`${API}/health`).then((r) => r.json())])
      .then(([loadedUnits, loadedItems, health]) => { setUnits(loadedUnits); const sortedItems = [...loadedItems].sort((a, b) => Number(a.item_id.includes("Corrupted")) - Number(b.item_id.includes("Corrupted"))); setItems(sortedItems.filter((item, index) => !item.name_ko.startsWith("tft_item_") && sortedItems.findIndex((other) => other.name_ko === item.name_ko) === index)); setMeta(health.meta || {}); })
      .catch(() => setError("API에 연결할 수 없습니다. 백엔드를 먼저 실행해 주세요."));
    fetch("/lolchess_unit_items.json").then((r) => r.ok ? r.json() : {}).then(setUnitItemSnapshot).catch(() => {});
    fetch(`${API}/patch-notes`).then((r) => r.ok ? r.json() : null).then(setPatch).catch(() => {});
  }, []);

  const traits = useMemo(() => [...new Set(units.flatMap((unit) => JSON.parse(unit.traits_json || "[]")))].sort((a, b) => a.localeCompare(b, "ko")), [units]);
  const filtered = useMemo(
    () => units.filter((unit) => unit.cost >= 1 && unit.cost <= 5)
      .filter((unit) => (unit.name_ko || unit.name_en).toLowerCase().includes(query.toLowerCase()))
      .filter((unit) => !costFilter || unit.cost === costFilter)
      .filter((unit) => !traitFilter || JSON.parse(unit.traits_json || "[]").includes(traitFilter))
      .filter((unit) => !selected.includes(unit.unit_id))
      .sort((a, b) => (a.cost || 0) - (b.cost || 0) || (a.name_ko || a.name_en).localeCompare(b.name_ko || b.name_en, "ko")),
    [units, query, selected, costFilter, traitFilter],
  );

  useEffect(() => {
    if (selected.length < 1) { setResults([]); return; }
    const controller = new AbortController();
    fetch(`${API}/recommend/units`, { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ unit_ids: selected }), signal: controller.signal })
      .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
      .then((payload) => { setResults(payload.recommendations); setError(""); })
      .catch((e) => { if (e.name !== "AbortError") setError("추천을 불러오지 못했습니다."); });
    return () => controller.abort();
  }, [selected]);

  useEffect(() => {
    if (!selectedItems.length) { setItemResults([]); return; }
    const controller = new AbortController();
    fetch(`${API}/recommend/items`, { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item_ids: selectedItems }), signal: controller.signal })
      .then((r) => r.json()).then((payload) => setItemResults(payload.recommendations || []))
      .catch((e) => { if (e.name !== "AbortError") setError("아이템 추천을 불러오지 못했습니다."); });
    return () => controller.abort();
  }, [selectedItems]);

  const loadPatches = async () => {
    const response = await fetch(`${API}/patch-notes`);
    const payload = await response.json();
    setPatch(payload);
  };

  const patchGroups = ["특성", "유닛", "증강", "그 외"];
  const patchDirection = (change) => {
    if (/buff|상향|강화/i.test(change.type)) return "up";
    if (/nerf|하향|약화/i.test(change.type)) return "down";
    const directions = [];
    for (const [index, arrow] of [...change.text.matchAll(/⇒|→|->/g)].entries()) {
      const start = arrow.index;
      const end = [...change.text.matchAll(/⇒|→|->/g)][index + 1]?.index ?? change.text.length;
      const before = change.text.slice(0, start).split(/⇒|→|->/).at(-1);
      const after = change.text.slice(start + arrow[0].length, end);
      const oldValues = [...before.matchAll(/\d+(?:\.\d+)?/g)].map(([value]) => Number(value));
      const newValues = [...after.matchAll(/\d+(?:\.\d+)?/g)].map(([value]) => Number(value));
      if (!oldValues.length || oldValues.length !== newValues.length) continue;
      const delta = newValues.reduce((sum, value, i) => sum + Math.sign(value - oldValues[i]), 0);
      if (delta) directions.push(/비용|골드/i.test(before) ? -Math.sign(delta) : Math.sign(delta));
    }
    const up = directions.includes(1);
    const down = directions.includes(-1);
    if (up && down) return "mixed";
    if (up) return "up";
    if (down) return "down";
    return /상향|강화|buff/i.test(change.text) ? "up" : /하향|약화|nerf/i.test(change.text) ? "down" : "change";
  };
  const groupedChanges = patchGroups.map((group) => ({
    group,
    changes: (patch?.changes || []).filter((change) => {
      const text = `${change.type} ${change.text}`;
      const category = /특성|trait|synergy/i.test(text) ? "특성"
        : /유닛|챔피언|champion|unit/i.test(text) ? "유닛"
        : /증강|augment/i.test(text) ? "증강" : "그 외";
      return category === group;
    }),
  }));

  return <main>
    <header>
      <p className="eyebrow">TFT NEWBIE HELPER</p>
      <h1>내 유닛으로 갈 덱 찾기</h1>
      <p>보유 챔피언과 아이템으로 갈 수 있는 덱을 찾아보세요.</p>
      <nav className="main-nav" aria-label="메뉴">
        <button className={page === "unitDecks" ? "active" : ""} aria-current={page === "unitDecks" ? "page" : undefined} onClick={() => setPage("unitDecks")}>덱 추천(유닛)</button>
        <button className={page === "itemDecks" ? "active" : ""} aria-current={page === "itemDecks" ? "page" : undefined} onClick={() => setPage("itemDecks")}>덱 추천(아이템)</button>
        <button className={page === "patch" ? "active" : ""} aria-current={page === "patch" ? "page" : undefined} onClick={() => setPage("patch")}>패치 변경점</button>
      </nav>
    </header>
    {page !== "patch" ? <div className="workspace">
      <div className="input-column">
    {!meta.reference_comp_n && !meta.sample_n && <div className="notice">아직 추천 덱 데이터가 없습니다. 조합 스냅샷을 저장하면 추천이 표시됩니다.</div>}
    {meta.reference_comp_n && <p>{meta.reference_source || "저장된"} 덱 {meta.reference_comp_n}개 · {meta.reference_updated_at?.slice(0, 10)} 저장</p>}
    {page === "unitDecks" ? <>
    <section className="panel">
      <h2>보유 유닛 <small>({selected.length}/10 · 1개 이상 필요)</small></h2>
      <div className="selected">{selected.map((id) => <span className="unit-input" key={id}><button onClick={() => { setSelected(selected.filter((x) => x !== id)); setStars(({ [id]: _, ...rest }) => rest); }}>{units.find((u) => u.unit_id === id)?.name_ko || id} ×</button><button className="star" onClick={() => setStars({ ...stars, [id]: (stars[id] || 1) % 3 + 1 })}>{stars[id] || 1}★</button></span>)}</div>
      <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="유닛 검색" />
      <div className="unit-filters" aria-label="챔피언 필터">
        <div className="cost-filters">{[0, 1, 2, 3, 4, 5].map((cost) => <button key={cost} className={`cost-${cost} ${costFilter === cost ? "active" : ""}`} aria-pressed={costFilter === cost} onClick={() => setCostFilter(cost)}>{cost ? `${cost}코스트` : "전체"}</button>)}</div>
        <select aria-label="상징 필터" value={traitFilter} onChange={(e) => setTraitFilter(e.target.value)}><option value="">전체 상징·특성</option>{traits.map((trait) => <option key={trait} value={trait}>{trait}</option>)}</select>
      </div>
      <div className="suggestions">{filtered.map((unit) => <button className={`pick cost-${unit.cost || 1}`} disabled={selected.length >= 10} key={unit.unit_id} onClick={() => { setSelected([...selected, unit.unit_id]); setStars({ ...stars, [unit.unit_id]: 1 }); }} title={`${unit.cost}코스트 · ${JSON.parse(unit.traits_json || "[]").join(" · ")}`}>{iconUrl(unit.icon, unit.unit_id) && <img src={iconUrl(unit.icon, unit.unit_id)} alt="" loading="lazy" onError={(e) => { e.currentTarget.hidden = true; }} />}<span>{unit.name_ko || unit.name_en}</span></button>)}</div>
      {selected.length < 1 && <p>유닛을 선택하면 추천 덱을 표시합니다.</p>}
      {error && <p className="error">{error}</p>}
    </section>
    </> : <>
    <section className="panel">
      <h2>보유 아이템 <small>({selectedItems.length}/20)</small></h2>
      <div className="selected">{selectedItems.map((id, index) => <button key={`${id}-${index}`} onClick={() => setSelectedItems(selectedItems.filter((_, i) => i !== index))}>{items.find((item) => item.item_id === id)?.name_ko || id} ×</button>)}</div>
      <input value={itemQuery} onChange={(e) => setItemQuery(e.target.value)} placeholder="아이템 검색" />
      <div className="suggestions">{items.filter((item) => item.name_ko.toLowerCase().includes(itemQuery.toLowerCase())).slice(0, 30).map((item) => <button className="pick" disabled={selectedItems.length >= 20} key={item.item_id} onClick={() => setSelectedItems([...selectedItems, item.item_id])}>{iconUrl(item.icon) && <img src={iconUrl(item.icon)} alt="" loading="lazy" onError={(e) => { e.currentTarget.hidden = true; }} />}<span>{item.name_ko}</span></button>)}</div>
      <p>완성 아이템 1개 또는 조합 아이템 3개 이상을 선택하면 아이템 추천이 표시됩니다.</p>
    </section>
    </>}
      </div>
      <div className="results-column">
    {page === "unitDecks" ? <>
    <section>
      <div className="section-title"><h2>덱 추천(유닛)</h2><span>{results.length ? "점수순" : "입력 후 표시됩니다"}</span></div>
      {results.length ? <div className="cards">{results.map((item) => <article className="card" key={item.cluster_id}>
        <div className="card-heading"><h3>{item.deck_name.split(" · ").map((id) => units.find((u) => u.unit_id === id)?.name_ko || id).join(" · ")}</h3><span className="card-actions"><span className="match-score">유닛 {(item.score * 100).toFixed(1)}% 일치</span>{item.source_url && <a className="guide-link" href={item.source_url} target="_blank" rel="noreferrer">공략 페이지 열기 ↗</a>}<button className="copy-code-button" onClick={() => copyTeamCode(item)}>팀 코드 복사</button></span></div>{renderDeckPreview(item, units, items, unitItemSnapshot)}
        {item.avg_placement != null && <p>평균 등수 {item.avg_placement} · Top4 {(item.top4_rate * 100).toFixed(1)}% · 1등 {(item.win_rate * 100).toFixed(1)}%</p>}
      </article>)}</div> : <p>{selected.length >= 1 ? "선택한 유닛을 포함하는 덱이 없습니다." : "유닛을 선택하면 추천 덱을 표시합니다."}</p>}
    </section>
    </> : <>
    <section><div className="section-title"><h2>보유 아이템으로 잘 가는 덱</h2></div>
      {itemResults.length ? <div className="cards">{itemResults.map((deck) => <article className="card" key={deck.cluster_id}>
        <div className="card-heading"><h3>{deck.deck_name.split(" · ").map((id) => units.find((u) => u.unit_id === id)?.name_ko || id).join(" · ")}</h3><span className="card-actions"><span className="match-score">아이템 {(deck.score * 100).toFixed(1)}% 일치</span>{deck.source_url && <a className="guide-link" href={deck.source_url} target="_blank" rel="noreferrer">공략 페이지 열기 ↗</a>}<button className="copy-code-button" onClick={() => copyTeamCode(deck)}>팀 코드 복사</button></span></div>{renderDeckPreview(deck, units, items, unitItemSnapshot)}
        <p>관련 아이템: {deck.matched_items.map((id) => items.find((item) => item.item_id === id)?.name_ko || id).join(", ")}</p>
        <p>아이템 일치도 {(deck.score * 100).toFixed(1)}%{deck.avg_placement != null ? ` · 평균 등수 ${deck.avg_placement}` : ""}{deck.sample_n != null ? ` · 표본 ${deck.sample_n}` : ""}</p>
      </article>)}</div> : <p>{selectedItems.length ? "선택한 아이템과 일치하는 덱이 없습니다." : "아이템을 선택하면 추천 덱이 표시됩니다."}</p>}
    </section>
    </>}
      </div>
    </div> :
    <section className="panel patch"><div className="section-title"><h2>패치 변경점</h2><button onClick={loadPatches}>공식 노트 불러오기</button></div>
      {patch?.source ? <><p><a href={patch.source} target="_blank" rel="noreferrer">{patch.title || "최신 공식 패치 노트"}</a></p><div className="patch-groups">{groupedChanges.map(({ group, changes }) => <section className="patch-group" key={group}><h3>{group}</h3>{changes.length ? changes.map((change, index) => { const direction = patchDirection(change); return <article className="patch-change" key={`${change.type}-${index}`}><div className="patch-change-heading"><span className={`patch-direction ${direction}`}>{direction === "up" ? "▲ 상향" : direction === "down" ? "▼ 하향" : direction === "mixed" ? "◆ 혼합" : "● 변경"}</span><b>{change.type}</b></div><p>{change.text}</p></article>; }) : <p className="patch-empty">변경점이 없습니다.</p>}</section>)}</div></> : <p>최신 공식 패치 노트를 불러오고 있습니다.</p>}
    </section>}
    <footer>로컬·내부망 전용 · 출처의 패치·지역·티어 조건을 확인해 주세요.</footer>
    <footer className="riot">TFT 뉴비 헬퍼는 Riot Games의 보증을 받지 않으며 Riot Games 또는 관련 공식 기관의 견해를 반영하지 않습니다.</footer>
  </main>;
}

createRoot(document.getElementById("root")).render(<App />);
