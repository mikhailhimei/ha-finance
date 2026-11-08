import React, { useEffect, useState } from 'react';
import { createRoot, Root } from 'react-dom/client';
import './style.css';
import panelStyles from './style.css?inline';

import type { Expense, Data, Hass } from './types';
import { money, kopecks, total, today } from './finance';
import { Field, Metric, Modal } from './components';
import { Navigation } from './navigation';
import { ActionSheet, Pencil } from './action-sheet';
import { useDepositNavigation } from './use-deposit-navigation';
function App({hass,openSidebar=()=>{}}:{hass?:Hass;openSidebar?:()=>void}){
 const [data,setData]=useState<Data>({deposits:[]}),[tab,setTab]=useState(0),[error,setError]=useState(''),[busy,setBusy]=useState(false),[loaded,setLoaded]=useState(!hass);
 const [sheet,setSheet]=useState<'deposit'|Expense>();
 const [dialog,setDialog]=useState<'create'|'edit'|'expense'>(),[editing,setEditing]=useState<Expense>();
 const [kind,setKind]=useState<'expense'|'income'>('expense');
 const [deleting,setDeleting]=useState<Expense>();
 const {selected,navigate:setSelected,surface}=useDepositNavigation(Boolean(dialog||sheet||deleting));
 useEffect(()=>{setDialog(undefined);setSheet(undefined);setDeleting(undefined)},[selected]);
 useEffect(()=>{if(!hass)return;let unsubscribe:(()=>void)|undefined;let disposed=false;
 hass.callWS<Data>({type:'ha_finance/get'}).then(d=>{if(!disposed){setData(d);setLoaded(true)}}).catch(e=>setError(String(e.message||e)));
 hass.connection.subscribeMessage<Data>(d=>{if(!disposed)setData(d)},{type:'ha_finance/subscribe'}).then(fn=>{if(disposed)fn();else unsubscribe=fn}).catch(e=>setError(String(e.message||e)));
 return ()=>{disposed=true;unsubscribe?.()};},[hass]);
 const d=data.deposits.find(d=>d.id===selected); const t=d&&total(d);
 async function mutate(action:string,payload:object){setBusy(true);setError('');try{if(!hass)throw Error('Это предпросмотр. Для сохранения откройте панель в Home Assistant.');await hass.callWS({type:'ha_finance/mutate',action,payload});setDialog(undefined);setDeleting(undefined)}catch(e){setError(e instanceof Error?e.message:String(e))}finally{setBusy(false)}}
 function submit(e:React.FormEvent<HTMLFormElement>){e.preventDefault();const f=new FormData(e.currentTarget);try{if(dialog==='create'||dialog==='edit')void mutate(dialog==='create'?'create':'update',{deposit_id:d?.id,name:f.get('name'),principal:kopecks(String(f.get('amount')))});else void mutate('expense_save',{kind,deposit_id:d?.id,expense_id:editing?.id,name:f.get('name'),amount:kopecks(String(f.get('amount'))),date:f.get('date'),paid:f.get('paid')==='on'});}catch(e){setError(String(e))}}
 return <main ref={surface} className={`finance ${tab===0?'deposit-page':''}`}>{d&&tab===0?<header className="toolbar deposit-toolbar"><button className="icon-button" aria-label="Все вклады" onClick={()=>setSelected(undefined)}>←</button><div className="toolbar-title"><h1>{d.name}</h1></div><button className="icon-button" aria-label="Действия со вкладом" onClick={()=>setSheet('deposit')}><Pencil/></button></header>:<Navigation tab={tab} select={setTab} openSidebar={openSidebar}/>}

 {error&&!dialog&&<p className="error" role="alert">{error}</p>}{!hass&&<p className="notice">Предпросмотр интерфейса · сохранение доступно в Home Assistant</p>}
 {tab!==0?<section className="empty"><h2>{tab===1?'Распределение бюджета':'Заработная плата'}</h2><p>Этот раздел появится на следующем этапе.</p></section>:!loaded?<p>Загрузка вкладов…</p>:!d?<>{data.deposits.length===0?<section className="empty"><span className="empty-icon">₽</span><h2>Всё начинается с первого вклада</h2><p>Добавьте сумму и запланируйте, на что она пойдёт.</p></section>:<div className="cards">{data.deposits.map(deposit=>{const x=total(deposit);return <button className="card" key={deposit.id} onClick={()=>setSelected(deposit.id)}><h3>{deposit.name}<span>↗</span></h3><Metric label="Свободные деньги" value={x.available}/><div className="small-metrics"><Metric label="Общая сумма" value={x.principal}/><Metric label="Оплачено" value={x.actual}/><Metric label="Ожидается" value={x.expected}/></div></button>})}</div>}<div className="expense-dock"><button className="primary" onClick={()=>setDialog('create')}><span aria-hidden="true">＋</span> Создать вклад</button></div></>:<><section className="overview"><div className="donut" role="img" aria-label={`Общая сумма ${money(t!.principal)}, оплачено ${money(t!.actual)}`} style={{background:`conic-gradient(#578c73 ${Math.min(100,t!.principal?t!.actual/t!.principal*100:0)}%, #e8eee9 0)`}}><div><span>Общая сумма</span><strong>{money(t!.principal)}</strong></div></div><div className="summary"><Metric label="Фактические расходы" value={t!.actual}/><Metric label="Ожидаемые расходы" value={t!.expected}/><Metric label="Текущий остаток" value={t!.balance}/><Metric label="Свободные деньги" value={t!.available}/>{t!.available<0&&<p className="error">Плановые расходы превышают остаток.</p>}</div></section><section className="expenses" aria-label="Операции">{d.expenses.length===0?<p className="muted">Операций пока нет.</p>:d.expenses.slice().sort((a,b)=>a.date.localeCompare(b.date)).map(e=><div className="expense" key={e.id}><input type="checkbox" aria-label={`${e.kind==='income'?'Получено':'Оплачено'}: ${e.name}`} checked={e.paid} disabled={busy} onChange={ev=>void mutate('expense_paid',{deposit_id:d.id,expense_id:e.id,paid:ev.target.checked})}/><div className="expense-name"><strong>{e.name}</strong><span>{new Date(e.date+'T12:00:00').toLocaleDateString('ru-RU')} · {e.paid?(e.kind==='income'?'Получено':'Оплачено'):e.date<=today()?'Срок наступил':'Ожидается'}</span></div><strong className={e.kind==='income'?'income':e.paid?'paid':''}>{e.kind==='income'?'+':'−'}{money(e.amount)}</strong><button aria-label={`${e.paid?'Удалить операцию':'Действия с операцией'} ${e.name}`} onClick={()=>e.paid?setDeleting(e):setSheet(e)}>{e.paid?'×':<Pencil/>}</button></div>)}</section><div className="expense-dock"><button className="primary" onClick={()=>{setEditing(undefined);setKind('expense');setDialog('expense')}}><span aria-hidden="true">＋</span> Добавить</button></div></>}
 {sheet&&d&&<ActionSheet title={sheet==='deposit'?d.name:sheet.name} close={()=>setSheet(undefined)} actions={sheet==='deposit'?[
  {label:'Изменить',run:()=>setDialog('edit')},
  {label:'Удалить вклад',danger:true,run:()=>{if(confirm('Удалить вклад и все его расходы?'))void mutate('delete',{deposit_id:d.id})}},
 ]:[
  {label:'Изменить',run:()=>{setEditing(sheet);setKind(sheet.kind||'expense');setDialog('expense')}},
  {label:'Удалить',danger:true,run:()=>setDeleting(sheet)},
 ]}/>}

 {deleting&&d&&<ActionSheet title="Точно удалить?" description={`«${deleting.name}» — ${deleting.kind==='income'?'+':'−'}${money(deleting.amount)}. Суммы вклада будут пересчитаны.`} close={()=>setDeleting(undefined)} actions={[
  {label:busy?'Удаление…':'Удалить',danger:true,disabled:busy,run:()=>void mutate('expense_delete',{deposit_id:d.id,expense_id:deleting.id})},
  {label:'Отмена',run:()=>setDeleting(undefined)},
 ]}/>}
 {dialog&&<Modal title={{create:'Новый вклад',edit:'Изменить вклад',expense:editing?'Изменить операцию':'Добавить'}[dialog]} close={()=>setDialog(undefined)}>{error&&<p className="error" role="alert">{error}</p>}<form onSubmit={submit}>{dialog==='expense'&&<fieldset className="kind-switch"><legend>Тип операции</legend>{(['expense','income'] as const).map(value=><label key={value}><input type="radio" name="kind" value={value} checked={kind===value} onChange={()=>setKind(value)}/>{value==='expense'?'Расход':'Доход'}</label>)}</fieldset>}<Field label="Название" name="name" maxLength={150} required defaultValue={dialog==='edit'?d?.name:dialog==='expense'?editing?.name:''} autoFocus/><Field label={dialog==='expense'?'Сумма, ₽':'Начальная сумма вклада, ₽'} type="number" name="amount" min="0" max="1000000000000" step="0.01" required defaultValue={dialog==='edit'?d!.principal/100:dialog==='expense'&&editing?editing.amount/100:undefined}/>{dialog==='edit'&&<p className="muted">Начальная сумма без доходов и расходов. Все операции сохранятся.</p>}{dialog==='expense'&&<><Field label="Дата платежа" type="date" name="date" required defaultValue={editing?.date||today()}/><label className="check"><input type="checkbox" name="paid" defaultChecked={editing?.paid}/> {kind==='income'?'Уже получено':'Уже оплачено'}</label></>}<button className="primary" disabled={busy}>{busy?'Сохранение…':'Сохранить'}</button></form></Modal>}
 </main>
}
class FinancePanel extends HTMLElement {
 private root?:Root;
 private current?:Hass;
 private mount:HTMLDivElement;
 constructor(){
  super();
  const shadow=this.attachShadow({mode:'open'});
  const style=document.createElement('style');
  style.textContent=panelStyles;
  this.mount=document.createElement('div');
  shadow.append(style,this.mount);
 }
 set hass(value:Hass){if(this.current?.connection===value.connection)return;this.current=value;this.render()}
 connectedCallback(){this.render()}
 disconnectedCallback(){this.root?.unmount();this.root=undefined}
 private render(){
  if(!this.isConnected)return;
  this.root??=createRoot(this.mount);
  this.root.render(<App hass={this.current} openSidebar={()=>this.dispatchEvent(new CustomEvent('hass-toggle-menu',{bubbles:true,composed:true}))}/>);
 }
}
customElements.define('ha-finance-panel',FinancePanel);
const devRoot=document.getElementById('root');if(devRoot)createRoot(devRoot).render(<App/>);
