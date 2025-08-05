import React, { createContext, useContext } from "react";

const TabsContext = createContext();

export function Tabs({ value, onValueChange, children, className = "" }) {

import React, { createContext, useContext } from 'react';

const TabsContext = createContext();

export function Tabs({ value, onValueChange, children, className = '' }) {
 main
  return (
    <TabsContext.Provider value={{ value, onValueChange }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  );
}

export function TabsList({ children, className = "" }) {
  return <div className={className}>{children}</div>;
}

export function TabsTrigger({ value, children, className = "", ...props }) {
  const ctx = useContext(TabsContext);
  const active = ctx.value === value;
  const activeClass = active
    ? "border-b-2 border-blue-500 text-blue-600"
    : "text-gray-600";

export function TabsList({ children, className = '' }) {
  return <div className={className}>{children}</div>;
}

export function TabsTrigger({ value, children, className = '', ...props }) {
  const ctx = useContext(TabsContext);
  const active = ctx.value === value;
  const activeClass = active ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-600';
 main
  return (
    <button
      className={`${activeClass} px-3 py-2 text-sm ${className}`}
      onClick={() => ctx.onValueChange(value)}
      {...props}
    >
      {children}
    </button>
  );
}

export function TabsContent({ value, children, className = "" }) {

export function TabsContent({ value, children, className = '' }) {
 main
  const ctx = useContext(TabsContext);
  if (ctx.value !== value) return null;
  return <div className={className}>{children}</div>;
}
