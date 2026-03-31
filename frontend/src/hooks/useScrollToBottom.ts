import { useEffect, useRef } from "react";

export function useScrollToBottom<T extends HTMLDivElement>(
  deps: React.DependencyList
) {
  const ref = useRef<T>(null);

  useEffect(() => {
    if (ref.current && ref.current.parentElement) {
      const parent = ref.current.parentElement;
      parent.scrollTop = parent.scrollHeight;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return ref;
}
