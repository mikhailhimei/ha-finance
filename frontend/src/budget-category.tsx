import { useEffect, useState, type Ref } from 'react';
import type { Budget, BudgetPart, Hass } from './types';
import { Field, Metric, Modal } from './components';
import { ActionSheet, Pencil } from './action-sheet';
import { kopecks, money } from './finance';

type Category=Budget['expenses'][number];
export function BudgetCategory({budgetId,category,hass,back,surface,setBlocked}:{budgetId:string;category:Category;hass?:Hass;back:()=>void;surface:Ref<HTMLElement>;setBlocked:(blocked:boolean)=>void}){
 const [open,setOpen]=useState(false),[editing,setEditing]=useState<BudgetPart>(),[actions,setActions]=useState<BudgetPart>(),[busy,setBusy]=useState(false),[error,setError]=useState('');
 useEffect(()=>{setBlocked(Boolean(open||actions));return ()=>setBlocked(false)},[open,actions,setBlocked]);
 const parts=category.children||[],allocated=parts.reduce((sum,p)=>sum+p.amount,0);
 async function mutate(action:string,payload:object){setBusy(true);setError('');try{if(!hass)throw Error('Откройте панель в Home Assistant');await hass.callWS({type:'ha_finance/mutate',action,payload:{budget_id:budgetId,expense_id:category.id,...payload}});setOpen(false)}catch(e){setError(e instanceof Error?e.message:String(e))}finally{setBusy(false)}}
 function submit(event:React.FormEvent<HTMLFormElement>){event.preventDefault();const form=new FormData(event.currentTarget);try{void mutate('budget_part_save',{part_id:editing?.id,name:form.get('name'),amount:kopecks(String(form.get('amount'))),comment:form.get('comment')})}catch(e){setError(e instanceof Error?e.message:String(e))}}
 return <section ref={surface} className="budget-page category-page"><header className="toolbar deposit-toolbar"><button className="icon-button" aria-label="Назад к тратам" onClick={back}>←</button><div className="toolbar-title"><h1>{category.name}</h1></div><span className="header-spacer"/></header>
 {error&&!open&&<p className="error" role="alert">{error}</p>}
 <section className="category-summary"><Metric label="Сумма категории" value={category.amount}/>{category.comment&&<p className="muted expense-comment">{category.comment}</p>}<div className="category-totals"><Metric label="Распределено" value={allocated}/><Metric label="Осталось распределить" value={category.amount-allocated}/></div></section>
 {allocated>category.amount&&<p className="error">Подтипы превышают сумму категории на {money(allocated-category.amount)}.</p>}
 <section className="category-parts" aria-label="Подтипы расходов">{parts.map(part=><div className="expense" key={part.id}><div className="expense-name"><strong>{part.name}</strong>{part.comment&&<span className="expense-comment">{part.comment}</span>}</div><strong>{money(part.amount)}</strong><button aria-label={`Действия с подтипом ${part.name}`} onClick={()=>setActions(part)}><Pencil/></button></div>)}</section>
 <div className="expense-dock"><button className="primary" onClick={()=>{setEditing(undefined);setError('');setOpen(true)}}>Добавить</button></div>
 {actions&&<ActionSheet title={actions.name} close={()=>setActions(undefined)} actions={[{label:'Изменить',run:()=>{setEditing(actions);setError('');setOpen(true)}},{label:'Удалить',danger:true,run:()=>void mutate('budget_part_delete',{part_id:actions.id})},{label:'Отмена',run:()=>setActions(undefined)}]}/>}
 {open&&<Modal bottom title={editing?'Изменить подтип':'Добавить подтип'} close={()=>{if(!busy)setOpen(false)}}>{error&&<p className="error" role="alert">{error}</p>}<form onSubmit={submit}><Field label="Наименование" name="name" required maxLength={150} autoFocus defaultValue={editing?.name}/><Field label="Сумма, ₽" name="amount" type="number" min="0" max="1000000000000" step="0.01" required defaultValue={editing?editing.amount/100:undefined}/><label className="field">Комментарий<textarea name="comment" rows={3} maxLength={1000} defaultValue={editing?.comment}/></label><button className="primary" disabled={busy}>{busy?'Сохранение…':'Сохранить'}</button></form></Modal>}
 </section>
}
