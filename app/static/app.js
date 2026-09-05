const $ = (id) => document.getElementById(id);
const EVENT_TABLE_LIMIT = 500;
let currentResult = null;

async function refreshReadiness() {
  const status = $("source-state-text");
  if (!status) return;
  try {
    const response = await fetch("/api/ready", {cache: "no-store"});
    status.textContent = response.ok ? "BGPReader runtime ready" : "Live analysis runtime unavailable";
  } catch (_) {
    status.textContent = "Live analysis runtime unavailable";
  }
}
refreshReadiness();

function isoLocal(date) {
  const p = (n) => String(n).padStart(2, "0");
  return `${date.getUTCFullYear()}-${p(date.getUTCMonth()+1)}-${p(date.getUTCDate())}T${p(date.getUTCHours())}:${p(date.getUTCMinutes())}`;
}
const endDefault = new Date();
const startDefault = new Date(endDefault.getTime() - 60 * 60 * 1000);
$("start").value = isoLocal(startDefault);
$("end").value = isoLocal(endDefault);

function escapeText(value) { return String(value ?? ""); }

function drawTimeline(points) {
  const box = $("timeline-chart");
  box.replaceChildren();
  if (!points.length) {
    const empty = document.createElement("p"); empty.className = "empty"; empty.textContent = "No event activity to chart."; box.append(empty); return;
  }
  const width = 760, height = 220, pad = {x:38,y:18,b:32}, plotH = height-pad.y-pad.b;
  const max = Math.max(1, ...points.flatMap(p => [p.announcements,p.withdrawals]));
  const step = (width-pad.x-12)/Math.max(points.length,1), bar = Math.max(4,Math.min(18,step*.3));
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns,"svg"); svg.setAttribute("viewBox",`0 0 ${width} ${height}`); svg.setAttribute("aria-hidden","true");
  for(let i=0;i<=4;i++){
    const y=pad.y+plotH*i/4; const line=document.createElementNS(ns,"line");
    line.setAttribute("x1",pad.x);line.setAttribute("x2",width);line.setAttribute("y1",y);line.setAttribute("y2",y);line.setAttribute("stroke","#e4e9eb");svg.append(line);
  }
  points.forEach((p,i)=>{
    const x=pad.x+i*step+step/2;
    [[p.announcements,"#126d61",-bar],[p.withdrawals,"#b83a42",1]].forEach(([v,color,offset])=>{
      const h=v/max*plotH, rect=document.createElementNS(ns,"rect");
      rect.setAttribute("x",x+offset);rect.setAttribute("y",pad.y+plotH-h);rect.setAttribute("width",bar-1);rect.setAttribute("height",h);rect.setAttribute("fill",color);rect.setAttribute("rx","2");svg.append(rect);
    });
    if(i===0||i===points.length-1||i===Math.floor(points.length/2)){
      const t=document.createElementNS(ns,"text");t.setAttribute("x",x);t.setAttribute("y",height-8);t.setAttribute("text-anchor","middle");t.textContent=p.time.slice(11,16);svg.append(t);
    }
  });
  box.append(svg);
}

function renderPaths(paths) {
  const list=$("path-list");list.replaceChildren();
  if(!paths.length){const li=document.createElement("li");li.textContent="No AS paths were returned.";list.append(li);return;}
  const max=Math.max(...paths.map(p=>p.count));
  paths.forEach((p,i)=>{
    const li=document.createElement("li"),code=document.createElement("code"),meta=document.createElement("div"),bar=document.createElement("div"),fill=document.createElement("i");
    code.textContent=p.path;meta.className="path-meta";
    const pathLabel=document.createElement("span"),countLabel=document.createElement("span");
    pathLabel.textContent=`Path ${i+1}`;countLabel.textContent=`${p.count} observations`;meta.append(pathLabel,countLabel);
    bar.className="path-bar";fill.style.width=`${p.count/max*100}%`;bar.append(fill);li.append(code,meta,bar);list.append(li);
  });
}

function renderEvents(events, filter="all") {
  const body=$("event-body");body.replaceChildren();
  const rows=events.filter(e=>filter==="all"||e.type===filter);$("empty-events").hidden=rows.length>0;
  const visibleRows=rows.slice(0,EVENT_TABLE_LIMIT);
  visibleRows.forEach(e=>{
    const tr=document.createElement("tr");
    const values=[e.timestamp.replace("T"," ").replace("Z",""),e.type,e.collector,`AS${e.peer_asn}`,e.origin_asn?`AS${e.origin_asn}`:"-",e.as_path||"-"];
    values.forEach((v,i)=>{const td=document.createElement("td");if(i===1){const s=document.createElement("span");s.className=`event-pill ${e.type.toLowerCase()}`;s.textContent=e.type==="A"?"ANNOUNCE":"WITHDRAW";td.append(s);}else if(i===5){const c=document.createElement("code");c.textContent=v;td.append(c);}else td.textContent=v;tr.append(td);});body.append(tr);
  });
  const note=$("event-count-note");
  if(note){
    if(rows.length>EVENT_TABLE_LIMIT){note.textContent=`Showing ${EVENT_TABLE_LIMIT.toLocaleString()} of ${rows.length.toLocaleString()} matching events. Export JSON includes all collected events.`;}
    else{note.textContent=`Showing ${rows.length.toLocaleString()} matching event${rows.length===1?"":"s"}.`}
  }
}

function render(data){
  currentResult=data;$("results").hidden=false;$("prefix-label").textContent=data.prefix;$("source-note").textContent=data.source_note;
  $("mode-badge").textContent=data.mode;$("severity-label").textContent=data.severity;$("finding").dataset.severity=data.severity;$("finding-text").textContent=data.finding;
  Object.entries(data.metrics).forEach(([k,v])=>{const el=$("m-"+k);if(el)el.textContent=v.toLocaleString();});
  drawTimeline(data.timeline);renderPaths(data.paths);renderEvents(data.events);$("event-filter").value="all";$("results").scrollIntoView({behavior:"smooth",block:"start"});
}

$("analysis-form").addEventListener("submit",async(e)=>{
  e.preventDefault();$("form-error").hidden=true;$("results").hidden=true;$("loading").hidden=false;
  const projects=[...document.querySelectorAll('input[name="project"]:checked')].map(x=>x.value);
  const payload={resource:$("resource").value.trim(),start:$("start").value+":00Z",end:$("end").value+":00Z",projects,mode:$("mode").value};
  try{
    const response=await fetch("/api/analyze",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
    const data=await response.json();if(!response.ok)throw new Error(typeof data.detail==="string"?data.detail:(data.detail?.[0]?.msg||"Analysis failed"));render(data);
  }catch(err){$("form-error").textContent=escapeText(err.message);$("form-error").hidden=false;}finally{$("loading").hidden=true;}
});
$("event-filter").addEventListener("change",e=>currentResult&&renderEvents(currentResult.events,e.target.value));
$("export-json").addEventListener("click",()=>{if(!currentResult)return;const blob=new Blob([JSON.stringify(currentResult,null,2)],{type:"application/json"}),a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=`bgp-analysis-${currentResult.prefix.replaceAll("/","_")}.json`;a.click();URL.revokeObjectURL(a.href);});
$("copy-summary").addEventListener("click",async()=>{if(!currentResult)return;const m=currentResult.metrics,text=`BGP analysis for ${currentResult.prefix}\nSeverity: ${currentResult.severity}\n${currentResult.finding}\nEvents: ${m.events}; withdrawals: ${m.withdrawals}; announcements: ${m.announcements}; collectors: ${m.collectors}.\nSource: ${currentResult.source_note}`;await navigator.clipboard.writeText(text);$("copy-summary").textContent="Copied";setTimeout(()=>$("copy-summary").textContent="Copy summary",1600);});
