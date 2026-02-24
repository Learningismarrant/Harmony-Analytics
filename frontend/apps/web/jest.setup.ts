import "@testing-library/jest-dom";

/**
 * DataTransfer polyfill for jsdom.
 *
 * jsdom v26 (jest-environment-jsdom v30) implements DataTransfer internally but
 * does not expose it as a global constructor. Drag-drop tests that call
 * `new DataTransfer()` or `new DragEvent("dragover", { dataTransfer: ... })`
 * need this polyfill.
 */
if (typeof globalThis.DataTransfer === "undefined") {
  class DataTransferItemList {
    private items: DataTransferItem[] = [];
    get length() { return this.items.length; }
    add() { return null; }
    remove() {}
    clear() { this.items = []; }
    [Symbol.iterator]() { return this.items[Symbol.iterator](); }
  }

  globalThis.DataTransfer = class DataTransfer {
    dropEffect: string = "none";
    effectAllowed: string = "all";
    files = { length: 0 } as unknown as FileList;
    items = new DataTransferItemList() as unknown as DataTransferItemList & globalThis.DataTransferItemList;
    types: string[] = [];
    getData(_format: string) { return ""; }
    setData(_format: string, _data: string) {}
    clearData(_format?: string) {}
    setDragImage(_image: Element, _x: number, _y: number) {}
  } as unknown as typeof DataTransfer;
}

/**
 * React.use() polyfill for Jest + React 18.3.x CJS environment.
 *
 * Next.js 15's App Router passes params as a Promise and uses React.use()
 * to unwrap them. React 18.3.1's CJS bundle does not expose `use()` in the
 * test runtime. This polyfill makes synchronously-resolvable thenables
 * (e.g. Promise.resolve(value)) work without Suspense.
 */
const React = require("react");
if (!React.use) {
  // Track resolved values for already-settled promises
  const cache = new WeakMap<object, unknown>();

  React.use = function use<T>(resource: T | PromiseLike<T>): T {
    if (
      resource !== null &&
      typeof resource === "object" &&
      typeof (resource as PromiseLike<T>).then === "function"
    ) {
      const promise = resource as PromiseLike<T>;

      if (cache.has(promise)) {
        return cache.get(promise) as T;
      }

      // Eagerly subscribe — Promise.resolve() schedules microtasks synchronously
      // so by the time React renders the tree the value is typically available.
      let resolved: T;
      let didResolve = false;

      promise.then((v) => {
        resolved = v;
        didResolve = true;
        cache.set(promise, v);
      });

      if (didResolve) return resolved!;

      // For tests that pass an unresolved promise, throw a meaningful error
      // rather than triggering Suspense (which requires a concurrent root).
      throw new Error(
        "[jest.setup] React.use() received an unresolved Promise. " +
          "Wrap the call in `await act(async () => { ... })` or pass " +
          "Promise.resolve(value) instead of a pending promise.",
      );
    }

    // Context objects and other non-thenables are returned as-is
    return resource as T;
  };
}
