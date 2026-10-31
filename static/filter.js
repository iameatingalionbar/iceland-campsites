/* Campsite filters: progressive enhancement. Without JS every card stays visible. */
(function(){
  var f=document.getElementById('filters'); if(!f) return;
  var cards=[].slice.call(document.querySelectorAll('.filterable .camp'));
  var marks=[].slice.call(document.querySelectorAll('.dir-map .mk'));
  var count=document.getElementById('count'), empty=document.getElementById('empty');
  var keys=['electricity','showers','dump','kitchen'];
  function fold(t){return t.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/ð/g,'d').replace(/þ/g,'th').replace(/æ/g,'ae').replace(/ö/g,'o');}
  cards.forEach(function(c){c._n=fold(c.dataset.name||'');});
  f.hidden=false;
  var p=new URLSearchParams(location.search);
  ['q','region','winter'].forEach(function(k){ if(p.get(k)!==null && f.elements[k]) f.elements[k].value=p.get(k); });
  keys.forEach(function(k){ if(p.get(k)==='yes') f.elements[k].checked=true; });
  function run(){
    var raw=f.elements.q.value.trim(), q=fold(raw), r=f.elements.region.value, w=f.elements.winter.value;
    var ws=w?w.split(','):null, need=keys.filter(function(k){return f.elements[k].checked;}), n=0, shown={};
    cards.forEach(function(c){
      var d=c.dataset, ok=(!q||c._n.indexOf(q)>-1)&&(!r||d.region===r)&&(!ws||ws.indexOf(d.winter)>-1)&&need.every(function(k){return d[k]==='yes';});
      c.hidden=!ok; if(ok){n++; shown[c.querySelector('a').getAttribute('href')]=1;}
    });
    marks.forEach(function(m){ m.classList.toggle('off', !shown[m.getAttribute('href')]); });
    count.textContent='Showing '+n+' of '+cards.length+' campsites';
    empty.hidden=n>0;
    var s=new URLSearchParams();
    if(raw) s.set('q',raw); if(r) s.set('region',r); if(w) s.set('winter',w);
    need.forEach(function(k){s.set(k,'yes');});
    var qs=s.toString(); history.replaceState(null,'',qs?'?'+qs:location.pathname);
  }
  f.addEventListener('input',run); f.addEventListener('change',run);
  f.addEventListener('submit',function(e){e.preventDefault();run();});
  f.addEventListener('reset',function(){setTimeout(run,0);});
  run();
})();
