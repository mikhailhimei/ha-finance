import type { Deposit } from './types';
export const money = (n:number) => new Intl.NumberFormat('ru-RU',{style:'currency',currency:'RUB',maximumFractionDigits:2}).format(n/100);
export const kopecks = (s:string) => {const n=Number(s.replace(',','.')); if(!Number.isFinite(n)||n<0) throw Error('Введите положительную сумму'); return Math.round(n*100)};
export const total = (d:Deposit) => {
 const income=d.expenses.filter(e=>e.kind==='income'&&e.paid).reduce((s,e)=>s+e.amount,0);
 const principal=d.principal+income;
 const actual=d.expenses.filter(e=>e.kind!=='income'&&e.paid).reduce((s,e)=>s+e.amount,0);
 const expected=d.expenses.filter(e=>e.kind!=='income'&&!e.paid).reduce((s,e)=>s+e.amount,0);
 return {principal,actual,expected,balance:principal-actual,available:principal-actual-expected};
};
export const today = () => new Date().toLocaleDateString('sv-SE');
