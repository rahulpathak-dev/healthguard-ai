"use client";

import React from "react";

import { useEffect, useState } from "react";
import type { Locale } from "@/lib/i18n";
import { locales } from "@/lib/i18n";

export function LocaleSwitcher() {
  const [locale, setLocale] = useState<Locale>("en");
  useEffect(() => {
    const saved = window.localStorage.getItem("hg_locale") as Locale | null;
    if (saved && locales.includes(saved)) setLocale(saved);
  }, []);
  function change(next: Locale) {
    setLocale(next);
    window.localStorage.setItem("hg_locale", next);
    document.documentElement.lang = next;
  }
  return (
    <label className="locale-switcher">
      Language
      <select
        value={locale}
        onChange={(event) => change(event.target.value as Locale)}
        aria-label="Choose language"
      >
        <option value="en">English</option>
        <option value="hi">??????</option>
      </select>
    </label>
  );
}
