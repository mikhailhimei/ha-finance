import React from 'react';
import { money } from './finance';
export function Field({label,...props}:React.InputHTMLAttributes<HTMLInputElement>&{label:string}) {return <label className="field">{label}<input {...props}/></label>}
export function Metric({label,value}:{label:string;value:number}){return <div className="metric"><span>{label}</span><strong>{money(value)}</strong></div>}
export function Modal({title,children,close}:{title:string;children:React.ReactNode;close:()=>void}){return <div className="overlay" onClick={close}><section className="modal" role="dialog" aria-modal="true" aria-label={title} onClick={e=>e.stopPropagation()} onKeyDown={e=>{if(e.key==='Escape')close()}}><header><h2>{title}</h2><button aria-label="Закрыть" onClick={close}>×</button></header>{children}</section></div>}
