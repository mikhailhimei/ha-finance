import { useEffect, useRef, useState } from 'react';

const sections = ['Учёт использования вкладов', 'Распределение бюджета', 'Заработная плата', 'Долги', 'Настройки'];
function Burger(){return <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"/></svg>}

export function Navigation({tab,select,openSidebar}:{tab:number;select:(tab:number)=>void;openSidebar:()=>void}){
 const [open,setOpen]=useState(false);
 const trigger=useRef<HTMLButtonElement>(null);
 const menu=useRef<HTMLElement>(null);
 useEffect(()=>{
  if(!open)return;
  const container=menu.current!;
  const buttons=Array.from(container.querySelectorAll<HTMLButtonElement>('button'));
  (container.querySelector<HTMLButtonElement>('[aria-current="page"]')||buttons[0]).focus();
  const keydown=(event:KeyboardEvent)=>{
   if(event.key==='Escape'){event.preventDefault();setOpen(false)}
   if(event.key==='Tab'){
    const active=container.getRootNode() instanceof ShadowRoot?(container.getRootNode() as ShadowRoot).activeElement:document.activeElement;
    const index=buttons.indexOf(active as HTMLButtonElement);
    event.preventDefault();buttons[(index+(event.shiftKey?-1:1)+buttons.length)%buttons.length].focus();
   }
  };
  container.addEventListener('keydown',keydown);
  return ()=>{container.removeEventListener('keydown',keydown);trigger.current?.focus()};
 },[open]);
 return <><header className="toolbar">
  <button className="icon-button" aria-label="Открыть меню Home Assistant" onClick={openSidebar}><Burger/></button>
  <div className="toolbar-title"><h1>{tab===0?'Мои вклады':sections[tab]}</h1></div>
  <button ref={trigger} className="icon-button" aria-label="Открыть разделы финансов" aria-expanded={open} aria-haspopup="dialog" onClick={()=>setOpen(!open)}><Burger/></button>
 </header>
 {open&&<div className="navigation-backdrop" onClick={()=>setOpen(false)}><section ref={menu} className="section-menu" role="dialog" aria-modal="true" aria-label="Разделы финансов" onClick={e=>e.stopPropagation()}>
  <div className="sheet-handle" aria-hidden="true"/>
  <header><h2>Разделы финансов</h2><button className="icon-button" aria-label="Закрыть разделы" onClick={()=>setOpen(false)}>×</button></header>
  <nav aria-label="Разделы">{[0,1,3,2,4].map(index=><button key={index} aria-current={index===tab?'page':undefined} onClick={()=>{select(index);setOpen(false)}}><span>{sections[index]}</span><span aria-hidden="true">{index===tab?'✓':'→'}</span></button>)}</nav>
 </section></div>}
 </>
}
