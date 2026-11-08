import { useEffect, useState } from 'react';
import type { Budget, Data, Hass } from './types';
import { Field, Metric, Modal } from './components';
import { Navigation } from './navigation';
import { kopecks, money, today } from './finance';
import { Pencil, ActionSheet } from './action-sheet';
import { Skeleton } from './skeleton';
import { BudgetCategory } from './budget-category';
import { HoldCard } from './hold-card';
import { useDepositNavigation } from './use-deposit-navigation';

type Payment={id:string;name:string;date:string;amount:number};
export function Budgets({data,hass,selectTab,openSidebar,loading=false}:{loading?:boolean;data:Data;hass?:Hass;selectTab:(tab:number)=>void;openSidebar:()=>void}){
 const [dialog,setDialog]=useState<'budget'|'expense'|'clone'>(),[payments,setPayments]=useState<Payment[]>([]),[error,setError]=useState(''),[busy,setBusy]=useState(false),[loaded,setLoaded]=useState(false);
 const [budgetActions,setBudgetActions]=useState<Budget>(),[cloneSource,setCloneSource]=useState<Budget>();
 const [categoryBlocked,setCategoryBlocked]=useState(false);
 const [deletingBudget,setDeletingBudget]=useState<Budget>();
 const [editExpense,setEditExpense]=useState<Budget['expenses'][number]>(),[actions,setActions]=useState<Budget['expenses'][number]>();
 const {selected,navigate,surface}=useDepositNavigation(Boolean(dialog||actions||deletingBudget||budgetActions||categoryBlocked),'haFinanceBudget');
 const budget=data.budgets?.find(b=>b.id===selected?.split('/')[0]);
 const month=budget?.month||today().slice(0,7);
 useEffect(()=>{setDialog(undefined);setActions(undefined);window.scrollTo(0,0)},[selected]);
 useEffect(()=>{let active=true;setLoaded(false);setError('');if(!hass)return;const [year,m]=month.split('-').map(Number);hass.callWS<Payment[]>({type:'ha_finance/budget_schedule',year,month:m}).then(p=>{if(active){setPayments(p);setLoaded(true)}}).catch(e=>{if(active)setError(String(e.message||e))});return ()=>{active=false}},[hass,month,data.workers,data.calendar_overrides]);
 const category=budget?.expenses.find(e=>e.id===selected?.split('/')[2]);
 const view=selected?.split('/')[1];
 const groups=Object.values(payments.reduce<Record<string,{date:string;payments:Payment[];amount:number}>>((result,p)=>{
  const group=result[p.date]??={date:p.date,payments:[],amount:0};group.payments.push(p);group.amount+=p.amount;return result;
 },{})).sort((a,b)=>a.date.localeCompare(b.date));
 const group=groups.find(g=>g.date===view);
 const sources=view&&view!=='all'?(group?.payments||[]):payments;
 const monthExpenses=budget?.expenses.filter(e=>e.month===month)||[];
 const expenses=view==='all'?monthExpenses:monthExpenses.filter(e=>sources.some(p=>p.id===e.payment_id));
 const income=sources.reduce((sum,p)=>sum+p.amount,0);
 const title=budget?(view==='all'?'Общий бюджет':view?new Date(view+'T12:00:00').toLocaleDateString('ru-RU'):budget.name):'';
 const spent=expenses.reduce((sum,e)=>sum+e.amount,0);
 async function mutate(action:string,payload:object){setBusy(true);setError('');try{if(!hass)throw Error('Откройте панель в Home Assistant');await hass.callWS({type:'ha_finance/mutate',action,payload});setDialog(undefined)}catch(e){setError(e instanceof Error?e.message:String(e))}finally{setBusy(false)}}
 function submit(event:React.FormEvent<HTMLFormElement>){event.preventDefault();const form=new FormData(event.currentTarget);try{if(dialog==='clone')void mutate('budget_clone',{budget_id:cloneSource!.id,month:form.get('month')});else if(dialog==='budget')void mutate('budget_create',{month:form.get('month')});else void mutate('budget_expense_save',{budget_id:budget!.id,expense_id:editExpense?.id,name:form.get('name'),amount:kopecks(String(form.get('amount'))),comment:form.get('comment'),month,payment_id:editExpense?.payment_id||(sources.length===1?sources[0].id:form.get('payment_id'))})}catch(e){setError(String(e))}}
 const renderExpense=(e:Budget['expenses'][number])=><div className="expense" key={e.id}><div className="expense-name"><button className="expense-category-link" aria-label={`Открыть категорию ${e.name}`} onClick={()=>navigate(`${budget!.id}/${view}/${e.id}`)}>{e.name}<span aria-hidden="true"> ↗</span></button>{e.comment&&<span className="expense-comment">{e.comment}</span>}{sources.length>1&&<span>{payments.find(p=>p.id===e.payment_id)?.name||'Источник дохода недоступен'}</span>}</div><strong>−{money(e.amount)}</strong><button aria-label={`Действия с тратой ${e.name}`} onClick={()=>setActions(e)}><Pencil/></button></div>;
 if(category&&budget)return <BudgetCategory budgetId={budget.id} category={category} hass={hass} back={()=>navigate(undefined)} surface={surface} setBlocked={setCategoryBlocked}/>;
 return <section ref={surface} className="budget-page">
 {budget?<header className="toolbar deposit-toolbar"><button className="icon-button" aria-label={view?"Назад к доходам":"Все бюджеты"} onClick={()=>navigate(undefined)}>←</button><div className="toolbar-title"><h1>{title}</h1></div><span className="header-spacer"/></header>:<Navigation tab={1} select={selectTab} openSidebar={openSidebar}/>}
 {budget&&(data.calendar_overrides?.[month.slice(0,4)]?!data.calendar_overrides[month.slice(0,4)].confirmed:Number(month.slice(0,4))>2027)&&<p className="notice">Предварительный календарь: будущие переносы выходных ещё не учтены.</p>}
 {error&&<p className="error" role="alert">{error}</p>}
 {!budget?<>{loading?<Skeleton variant="cards"/>:!data.budgets?.length?<div className="empty"><h2>Бюджетов пока нет</h2><p>Создайте бюджет и распределите будущие доходы.</p></div>:<div className="cards">{[...data.budgets].reverse().map(b=><HoldCard className="card" key={b.id} name={b.name} open={()=>navigate(b.id)} onHold={()=>setBudgetActions(b)}><h3>{b.name}<span>↗</span></h3></HoldCard>)}</div>}<div className="expense-dock"><button className="primary" disabled={loading} onClick={()=>setDialog('budget')}>Создать бюджет</button></div></>:<>

 {!loaded?<Skeleton variant={view?'overview':'periods'} count={4}/>:!view?<div className="budget-periods"><button onClick={()=>navigate(`${budget.id}/all`)}>Посмотреть общий<strong>{money(payments.reduce((s,p)=>s+p.amount,0)-monthExpenses.reduce((s,e)=>s+e.amount,0))}</strong></button>{groups.map(g=><button key={g.date} onClick={()=>navigate(`${budget.id}/${g.date}`)}><span>{new Date(g.date+'T12:00:00').toLocaleDateString('ru-RU',{day:'2-digit',month:'2-digit'})} · {g.payments.map(p=>p.name).join(', ')}</span><strong>{money(g.amount-monthExpenses.filter(e=>g.payments.some(p=>p.id===e.payment_id)).reduce((sum,e)=>sum+e.amount,0))}</strong></button>)}</div>:<>
 <section className="overview budget-overview"><div className="donut" role="img" aria-label={`Всего доход ${money(income)}, запланировано ${money(spent)}`} style={{background:`conic-gradient(#578c73 ${Math.min(100,income?spent/income*100:0)}%, #e8eee9 0)`}}><div><span>Доход всего</span><strong>{money(income)}</strong></div></div><div className="summary"><Metric label="Общие доходы" value={income}/><Metric label="Расходы по плану" value={spent}/><Metric label="Свободные деньги" value={income-spent}/></div></section>
 {spent>income&&<p className="error">Расходы превышают доход.</p>}
 <div className="budget-expenses">{view==='all'?<>{groups.map(g=>{
  const items=expenses.filter(e=>g.payments.some(p=>p.id===e.payment_id));
  const planned=items.reduce((sum,e)=>sum+e.amount,0);
  return <section className="budget-expense-group" key={g.date}><header><div><h2>{new Date(g.date+'T12:00:00').toLocaleDateString('ru-RU')}</h2><p className="muted">{g.payments.map(p=>p.name).join(', ')}</p></div></header><div className="group-metrics"><Metric label="Доход" value={g.amount}/><Metric label="Расходы" value={planned}/><Metric label="Свободно" value={g.amount-planned}/></div>{items.map(renderExpense)}</section>
 })}{expenses.some(e=>!payments.some(p=>p.id===e.payment_id))&&<section className="budget-expense-group"><h2>Без доступного источника</h2>{expenses.filter(e=>!payments.some(p=>p.id===e.payment_id)).map(renderExpense)}</section>}</>:expenses.map(renderExpense)}</div>

 <div className="expense-dock"><button className="primary" disabled={sources.length===0} onClick={()=>{setEditExpense(undefined);setDialog('expense')}}>Добавить трату</button></div>
 {sources.length===0&&<p className="muted">Сначала укажите доход во вкладке «Заработная плата».</p>}
 </>}
 </>}
 {budgetActions&&<ActionSheet title={budgetActions.name} close={()=>setBudgetActions(undefined)} actions={[
  {label:'Клонировать',run:()=>{setCloneSource(budgetActions);setDialog('clone')}},
  {label:'Удалить',danger:true,run:()=>setDeletingBudget(budgetActions)},
  {label:'Отмена',run:()=>setBudgetActions(undefined)},
 ]}/>}
 {deletingBudget&&<ActionSheet title="Удалить бюджет?" description={`«${deletingBudget.name}» и все его траты будут удалены.`} close={()=>setDeletingBudget(undefined)} actions={[
  {label:'Удалить',danger:true,run:()=>void mutate('budget_delete',{budget_id:deletingBudget.id})},{label:'Отмена',run:()=>setDeletingBudget(undefined)},
 ]}/>}
 {actions&&budget&&<ActionSheet title={actions.name} close={()=>setActions(undefined)} actions={[{label:'Изменить',run:()=>{setEditExpense(actions);setDialog('expense')}},{label:'Удалить',danger:true,run:()=>void mutate('budget_expense_delete',{budget_id:budget.id,expense_id:actions.id})},{label:'Отмена',run:()=>setActions(undefined)}]}/>}
 {dialog&&<Modal bottom title={dialog==='clone'?'Клонировать бюджет':dialog==='budget'?'Новый бюджет':editExpense?'Изменить трату':'Добавить трату'} close={()=>setDialog(undefined)}>{error&&<p className="error" role="alert">{error}</p>}<form onSubmit={submit}>{dialog!=='expense'?<Field label="Месяц и год" name="month" type="month" min="2025-01" max="2100-12" required defaultValue={today().slice(0,7)}/>:<Field label="Наименование" name="name" required maxLength={150} defaultValue={editExpense?.name} autoFocus/>}{dialog==='expense'&&<>{sources.length>1&&!editExpense&&<label className="field">Источник дохода<select name="payment_id" required>{sources.map(p=><option key={p.id} value={p.id}>{p.date} · {p.name}</option>)}</select></label>}<Field label="Сумма, ₽" name="amount" type="number" min="0" max="1000000000000" step="0.01" required defaultValue={editExpense?editExpense.amount/100:undefined}/><label className="field">Комментарий<textarea name="comment" maxLength={1000} rows={3} defaultValue={editExpense?.comment}/></label></>}<button className="primary" disabled={busy}>{busy?'Сохранение…':'Сохранить'}</button></form></Modal>}
 </section>
}
