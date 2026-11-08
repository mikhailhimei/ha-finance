import { useEffect, useRef } from 'react';

export function Pencil(){return <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m15 5 4 4M4 20l4-1L20 7a2.8 2.8 0 0 0-4-4L4 15z"/></svg>}
type Action={label:string;danger?:boolean;disabled?:boolean;run:()=>void};
export function ActionSheet({title,description,actions,close}:{title:string;description?:string;actions:Action[];close:()=>void}){
 const ref=useRef<HTMLElement>(null);
 useEffect(()=>{
  const sheet=ref.current!;
  const root=sheet.getRootNode();
  const previous=(root instanceof ShadowRoot?root.activeElement:document.activeElement) as HTMLElement|null;
  const buttons=Array.from(sheet.querySelectorAll<HTMLButtonElement>('button'));
  buttons[0]?.focus();
  const onKey=(e:KeyboardEvent)=>{
   if(e.key==='Escape'){e.preventDefault();close()}
   if(e.key==='Tab'){
    e.preventDefault();
    const active=root instanceof ShadowRoot?root.activeElement:document.activeElement;
    const index=buttons.indexOf(active as HTMLButtonElement);
    buttons[(index+(e.shiftKey?-1:1)+buttons.length)%buttons.length]?.focus();
   }
  };
  sheet.addEventListener('keydown',onKey);
  return ()=>{sheet.removeEventListener('keydown',onKey);if(previous?.isConnected)previous.focus()};
 },[close]);
 return <div className="navigation-backdrop" onClick={close}><section ref={ref} className="action-sheet" role="dialog" aria-modal="true" aria-label={title} onClick={e=>e.stopPropagation()}><div className="sheet-handle" aria-hidden="true"/><header><h2>{title}</h2><button className="icon-button" aria-label="Закрыть действия" onClick={close}>×</button></header>{description&&<p className="sheet-description">{description}</p>}<div className="sheet-actions">{actions.map(action=><button key={action.label} disabled={action.disabled} className={action.danger?'destructive':''} onClick={()=>{close();action.run()}}>{action.label}</button>)}</div></section></div>
}
