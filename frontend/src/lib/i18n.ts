import sk from "@/locales/sk/common.json";
import en from "@/locales/en/common.json";

export type Locale = "sk" | "en";
type Dict = typeof sk;

const dicts: Record<Locale, Dict> = { sk, en };

export function getDict(locale: Locale = "sk"): Dict {
  return dicts[locale] || dicts.sk;
}
