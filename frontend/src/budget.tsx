import { useEffect, useState } from 'react';
import type { Budget, Data, Hass } from './types';
import { Field, Metric, Modal } from './components';
import { Navigation } from './navigation';
import { kopecks, money, today } from './finance';
import { Pencil, ActionSheet } from './action-sheet';
import { HoldCard } from './hold-card';
import { useDepositNavigation } from './use-deposit-navigation';

type Payment={id:string;name:string;date:string;amount:number};
export function Budgets({data,hass,selectTab,openSidebar}:{data:Data;hass?:Hass;selectTab:(tab:number)=>void;openSidebar:()=>void}){
 const [dialog,setDialog]=useState<'budget'|'expense'>(),[payments,setPayments]=useState<Payment[]>([]),[error,setError]=useState(''),[busy,setBusy]=useState(false),[loaded,setLoaded]=useState(false);
 const [deletingBudget,setDeletingBudget]=useState<Budget>();
 const [paymentId,setPaymentId]=useState<string>(),[editExpense,setEditExpense]=useState<Budget['expenses'][number]>(),[actions,setActions]=useState<Budget['expenses'][number]>();
 const {selected,navigate,surface}=useDepositNavigation(Boolean(dialog||actions||deletingBudget),'haFinanceBudget');
 const budget=data.budgets?.find(b=>b.id===selected);
 const month=budget?.month||today().slice(0,7);
 useEffect(()=>{setPaymentId(undefined);setDialog(undefined)},[selected]);
 useEffect(()=>{let active=true;setLoaded(false);setError('');if(!hass)return;const [year,m]=month.split('-').map(Number);hass.callWS<Payment[]>({type:'ha_finance/budget_schedule',year,month:m}).then(p=>{if(active){setPayments(p);setLoaded(true)}}).catch(e=>{if(active)setError(String(e.message||e))});return ()=>{active=false}},[hass,month,data.workers]);
 const monthExpenses=budget?.expenses.filter(e=>e.month===month)||[];
 const expenses=paymentId?monthExpenses.filter(e=>e.payment_id===paymentId):monthExpenses;
 const payment=payments.find(p=>p.id===paymentId);
 const income=paymentId?(payment?.amount||0):payments.reduce((sum,p)=>sum+p.amount,0);
 const spent=expenses.reduce((sum,e)=>sum+e.amount,0);
 async function mutate(action:string,payload:object){setBusy(true);setError('');try{if(!hass)throw Error('Откройте панель в Home Assistant');await hass.callWS({type:'ha_finance/mutate',action,payload});setDialog(undefined)}catch(e){setError(e instanceof Error?e.message:String(e))}finally{setBusy(false)}}
 function submit(event:React.FormEvent<HTMLFormElement>){event.preventDefault();const form=new FormData(event.currentTarget);try{if(dialog==='budget')void mutate('budget_create',{month:form.get('month')});else void mutate('budget_expense_save',{budget_id:budget!.id,expense_id:editExpense?.id,name:form.get('name'),amount:kopecks(String(form.get('amount'))),comment:form.get('comment'),month,payment_id:editExpense?.payment_id||paymentId||form.get('payment_id')})}catch(e){setError(String(e))}}
 return <section ref={surface} className="budget-page">
 {budget?<header className="toolbar deposit-toolbar"><button className="icon-button" aria-label="Все бюджеты" onClick={()=>navigate(undefined)}>←</button><div className="toolbar-title"><h1>{budget.name}</h1></div><span className="header-spacer"/></header>:<Navigation tab={1} select={selectTab} openSidebar={openSidebar}/>}
 {error&&<p className="error" role="alert">{error}</p>}
 {!budget?<>{!data.budgets?.length?<div className="empty"><h2>Бюджетов пока нет</h2><p>Создайте бюджет и распределите будущие доходы.</p></div>:<div className="cards">{data.budgets.map(b=><HoldCard className="card" key={b.id} name={b.name} open={()=>navigate(b.id)} onHold={()=>setDeletingBudget(b)}><h3>{b.name}<span>↗</span></h3></HoldCard>)}</div>}<div className="expense-dock"><button className="primary" onClick={()=>setDialog('budget')}>Создать бюджет</button></div></>:<>

 {!loaded?<p className="muted">Загрузка доходов…</p>:<><div className="budget-periods"><button className={!paymentId?'selected':''} onClick={()=>setPaymentId(undefined)}>Посмотреть общий<strong>{money(payments.reduce((s,p)=>s+p.amount,0)-monthExpenses.reduce((s,e)=>s+e.amount,0))}</strong></button>{payments.map(p=><button key={p.id} className={paymentId===p.id?'selected':''} onClick={()=>setPaymentId(p.id)}><span>{new Date(p.date+'T12:00:00').toLocaleDateString('ru-RU',{day:'2-digit',month:'2-digit'})} · {p.name}</span><strong>{money(p.amount-monthExpenses.filter(e=>e.payment_id===p.id).reduce((sum,e)=>sum+e.amount,0))}</strong></button>)}</div>
 <section className="overview budget-overview"><div className="donut" role="img" aria-label={`Всего доход ${money(income)}, запланировано ${money(spent)}`} style={{background:`conic-gradient(#578c73 ${Math.min(100,income?spent/income*100:0)}%, #e8eee9 0)`}}><div><span>Доход всего</span><strong>{money(income)}</strong></div></div><div className="summary"><Metric label="Общие доходы" value={income}/><Metric label="Расходы по плану" value={spent}/><Metric label="Свободные деньги" value={income-spent}/></div></section>
 {spent>income&&<p className="error">Расходы превышают доход.</p>}
 <div className="budget-expenses">{expenses.length===0?<p className="muted">Трат пока нет. Укажите, на что пойдут деньги.</p>:expenses.map(e=><div className="expense" key={e.id}><div className="expense-name"><strong>{e.name}</strong>{e.comment&&<span className="expense-comment">{e.comment}</span>}{!paymentId&&<span>{payments.find(p=>p.id===e.payment_id)?.name||'Источник дохода недоступен'}</span>}</div><strong>−{money(e.amount)}</strong><button aria-label={`Действия с тратой ${e.name}`} onClick={()=>setActions(e)}><Pencil/></button></div>)}</div>
 <div className="expense-dock"><button className="primary" disabled={payments.length===0} onClick={()=>{setEditExpense(undefined);setDialog('expense')}}>Добавить трату</button></div>
 {payments.length===0&&<p className="muted">Сначала укажите доход во вкладке «Заработная плата».</p>}
 </>}
 </>}
 {deletingBudget&&<ActionSheet title="Удалить бюджет?" description={`«${deletingBudget.name}» и все его траты будут удалены.`} close={()=>setDeletingBudget(undefined)} actions={[
  {label:'Удалить',danger:true,run:()=>void mutate('budget_delete',{budget_id:deletingBudget.id})},{label:'Отмена',run:()=>setDeletingBudget(undefined)},
 ]}/>}
 {actions&&budget&&<ActionSheet title={actions.name} close={()=>setActions(undefined)} actions={[{label:'Изменить',run:()=>{setEditExpense(actions);setDialog('expense')}},{label:'Удалить',danger:true,run:()=>void mutate('budget_expense_delete',{budget_id:budget.id,expense_id:actions.id})},{label:'Отмена',run:()=>setActions(undefined)}]}/>}
 {dialog&&<Modal bottom title={dialog==='budget'?'Новый бюджет':editExpense?'Изменить трату':'Добавить трату'} close={()=>setDialog(undefined)}>{error&&<p className="error" role="alert">{error}</p>}<form onSubmit={submit}>{dialog==='budget'?<Field label="Месяц и год" name="month" type="month" min="2025-01" max="2027-12" required defaultValue={today().slice(0,7)}/>:<Field label="Наименование" name="name" required maxLength={150} defaultValue={editExpense?.name} autoFocus/>}{dialog==='expense'&&<>{!paymentId&&!editExpense&&<label className="field">Источник дохода<select name="payment_id" required>{payments.map(p=><option key={p.id} value={p.id}>{p.date} · {p.name}</option>)}</select></label>}<Field label="Сумма, ₽" name="amount" type="number" min="0" max="1000000000000" step="0.01" required defaultValue={editExpense?editExpense.amount/100:undefined}/><label className="field">Комментарий<textarea name="comment" maxLength={1000} rows={3} defaultValue={editExpense?.comment}/></label></>}<button className="primary" disabled={busy}>{busy?'Сохранение…':'Сохранить'}</button></form></Modal>}
 </section>
}
