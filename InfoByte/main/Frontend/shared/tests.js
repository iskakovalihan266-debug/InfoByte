const screen = document.querySelector('#screen');
const error = document.querySelector('#error');
const base = '/api/test-attempts';
let id, state, index, busy = false;

function el(tag, text = '') {
  const node = document.createElement(tag);
  node.textContent = text;
  return node;
}
async function run(action) {
  if (busy) return;
  busy = true;
  screen.inert = true;
  error.textContent = '';
  try { await action(); }
  catch (e) { error.textContent = e.message; }
  finally { busy = false; screen.inert = false; }
}
function button(text, action, primary = false) {
  const node = el('button', text);
  if (primary) node.className = 'primary';
  node.onclick = () => run(action);
  return node;
}
async function api(path, method = 'GET', body) {
  const res = await fetch(path, {method, headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
  if (res.status === 401) location.replace('/infobyte-auth/login.html');
  const data = await res.json();
  if (!res.ok) throw Error(data.detail || 'Сұрау орындалмады.');
  return data;
}
function select(box, label, values) {
  const wrap = el('label', label), field = el('select');
  for (const [value,text] of values) field.add(new Option(text,value));
  wrap.append(field); box.append(wrap);
  return field;
}
async function home() {
  const topics = await api('/api/test-topics');
  const history = await api(base);
  const box = el('section');
  const topic = select(box,'Тақырып',[['0','Аралас тест'],...topics.map((t,i)=>[i+1,t])]);
  const count = select(box,'Сұрақ саны',[5,10,20].map(n=>[n,n]));
  box.append(button('Тестті бастау',async()=>{
    const created = await api(base,'POST',{topic:Number(topic.value),count:Number(count.value)});
    await open(created.id);
  },true));
  screen.replaceChildren(box);
  if (history.length) {
    const list = el('section'); list.append(el('h2','Менің тесттерім'));
    for (const a of history) {
      const row = el('p');
      row.append(button(a.count+' сұрақ · '+(a.finished?'Нәтижені көру':'Жалғастыру'),()=>open(a.id)));
      list.append(row);
    }
    screen.append(list);
  }
}
async function open(key) {
  state = await api(base+'/'+key); id = key;
  index = Math.max(0,state.questions.findIndex(q=>q.choice===null));
  draw();
}
function draw() {
  const rows = state.questions, box = el('section');
  screen.replaceChildren(box);
  if (state.finished) {
    box.append(el('h2','Нәтиже: '+state.score+' / '+rows.length+' · '+Math.round(100*state.score/rows.length)+'%'));
    for (const [i,q] of rows.entries()) {
      const detail = el('details'), prompt = el('p',q.text);
      prompt.className = 'question';
      detail.append(el('summary',(i+1)+'-сұрақ · '+(q.choice===q.key?'Дұрыс':'Қате')),prompt,
        el('p','Сенің жауабың: '+q.options[q.choice]),el('p','Дұрыс жауап: '+q.options[q.key]));
      box.append(detail);
    }
    if (state.score<rows.length) box.append(button('Қателерді қайталау',async()=>open((await api(base+'/'+id+'/retry','POST')).id)));
    box.append(button('Жаңа тест',home,true)); return;
  }
  const q = rows[index], prompt = el('h2',q.text), options = el('div'), actions = el('div');
  prompt.className='question'; options.className='options'; actions.className='actions';
  const bar = el('progress'); bar.max = rows.length; bar.value = rows.filter(r=>r.choice!==null).length;
  bar.setAttribute('aria-label','Жауап берілген сұрақтар');
  box.append(el('p',(index+1)+' / '+rows.length+' сұрақ · '+q.level),bar,prompt,options,actions);
  q.options.forEach((text,i)=>{
    const b = button('ABCD'[i]+') '+text,async()=>{
      state = await api(base+'/'+id+'/answers','PATCH',{question:q.id,choice:i}); draw();
    });
    b.setAttribute('aria-pressed',String(q.choice===i)); options.append(b);
  });
  const prev=button('← Алдыңғы',()=>{index--;draw();}); prev.disabled=index===0;
  actions.append(prev,index<rows.length-1 ? button('Келесі →',()=>{index++;draw();},true)
    : button('Тестті аяқтау',async()=>{
      const missing=rows.findIndex(r=>r.choice===null);
      if (missing>=0) {index=missing;draw();error.textContent='Осы сұраққа жауап беріңіз.';return;}
      state=await api(base+'/'+id+'/submit','POST');draw();
    },true));
}
run(home);

