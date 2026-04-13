import { defineStore } from 'pinia';
import type { RouteLocationNormalizedLoaded } from 'vue-router';

interface TagView {
  name?: string;
  path: string;
  title?: string;
  meta?: {
    title?: string;
    affix?: boolean;
    noCache?: boolean;
    link?: string;
  };
}

interface TagsViewState {
  visitedViews: TagView[];
  cachedViews: string[];
  iframeViews: TagView[];
}

const useTagsViewStore = defineStore('tags-view', {
  state: (): TagsViewState => ({
    visitedViews: [],
    cachedViews: [],
    iframeViews: [],
  }),
  actions: {
    addView(view: TagView) {
      this.addVisitedView(view);
      this.addCachedView(view);
    },
    addIframeView(view: TagView) {
      if (this.iframeViews.some((v) => v.path === view.path)) return;
      this.iframeViews.push(
        Object.assign({}, view, {
          title: view.meta?.title || 'no-name',
        })
      );
    },
    addVisitedView(view: TagView) {
      if (this.visitedViews.some((v) => v.path === view.path)) return;
      this.visitedViews.push(
        Object.assign({}, view, {
          title: view.meta?.title || 'no-name',
        })
      );
    },
    addCachedView(view: TagView) {
      if (!view.name || this.cachedViews.includes(view.name)) return;
      if (!view.meta?.noCache) {
        this.cachedViews.push(view.name);
      }
    },
    delView(view: TagView) {
      return new Promise((resolve) => {
        this.delVisitedView(view);
        this.delCachedView(view);
        resolve({
          visitedViews: [...this.visitedViews],
          cachedViews: [...this.cachedViews],
        });
      });
    },
    delVisitedView(view: TagView) {
      return new Promise((resolve) => {
        for (const [i, v] of this.visitedViews.entries()) {
          if (v.path === view.path) {
            this.visitedViews.splice(i, 1);
            break;
          }
        }
        this.iframeViews = this.iframeViews.filter((item) => item.path !== view.path);
        resolve([...this.visitedViews]);
      });
    },
    delIframeView(view: TagView) {
      return new Promise((resolve) => {
        this.iframeViews = this.iframeViews.filter((item) => item.path !== view.path);
        resolve([...this.iframeViews]);
      });
    },
    delCachedView(view: TagView) {
      return new Promise((resolve) => {
        if (!view.name) {
          resolve([...this.cachedViews]);
          return;
        }
        const index = this.cachedViews.indexOf(view.name);
        index > -1 && this.cachedViews.splice(index, 1);
        resolve([...this.cachedViews]);
      });
    },
    delOthersViews(view: TagView) {
      return new Promise((resolve) => {
        this.delOthersVisitedViews(view);
        this.delOthersCachedViews(view);
        resolve({
          visitedViews: [...this.visitedViews],
          cachedViews: [...this.cachedViews],
        });
      });
    },
    delOthersVisitedViews(view: TagView) {
      return new Promise((resolve) => {
        this.visitedViews = this.visitedViews.filter((v) => {
          return v.meta?.affix || v.path === view.path;
        });
        this.iframeViews = this.iframeViews.filter((item) => item.path === view.path);
        resolve([...this.visitedViews]);
      });
    },
    delOthersCachedViews(view: TagView) {
      return new Promise((resolve) => {
        if (!view.name) {
          this.cachedViews = [];
          resolve([...this.cachedViews]);
          return;
        }
        const index = this.cachedViews.indexOf(view.name);
        if (index > -1) {
          this.cachedViews = this.cachedViews.slice(index, index + 1);
        } else {
          this.cachedViews = [];
        }
        resolve([...this.cachedViews]);
      });
    },
    delAllViews(view?: TagView) {
      return new Promise((resolve) => {
        this.delAllVisitedViews(view);
        this.delAllCachedViews(view);
        resolve({
          visitedViews: [...this.visitedViews],
          cachedViews: [...this.cachedViews],
        });
      });
    },
    delAllVisitedViews(view?: TagView) {
      return new Promise((resolve) => {
        const affixTags = this.visitedViews.filter((tag) => tag.meta?.affix);
        this.visitedViews = affixTags;
        this.iframeViews = [];
        resolve([...this.visitedViews]);
      });
    },
    delAllCachedViews(view?: TagView) {
      return new Promise((resolve) => {
        this.cachedViews = [];
        resolve([...this.cachedViews]);
      });
    },
    updateVisitedView(view: TagView) {
      for (let v of this.visitedViews) {
        if (v.path === view.path) {
          v = Object.assign(v, view);
          break;
        }
      }
    },
    delRightTags(view: TagView) {
      return new Promise((resolve) => {
        const index = this.visitedViews.findIndex((v) => v.path === view.path);
        if (index === -1) {
          return;
        }
        this.visitedViews = this.visitedViews.filter((item, idx) => {
          if (idx <= index || (item.meta && item.meta.affix)) {
            return true;
          }
          if (item.name) {
            const i = this.cachedViews.indexOf(item.name);
            if (i > -1) {
              this.cachedViews.splice(i, 1);
            }
          }
          if (item.meta?.link) {
            const fi = this.iframeViews.findIndex((v) => v.path === item.path);
            this.iframeViews.splice(fi, 1);
          }
          return false;
        });
        resolve([...this.visitedViews]);
      });
    },
    delLeftTags(view: TagView) {
      return new Promise((resolve) => {
        const index = this.visitedViews.findIndex((v) => v.path === view.path);
        if (index === -1) {
          return;
        }
        this.visitedViews = this.visitedViews.filter((item, idx) => {
          if (idx >= index || (item.meta && item.meta.affix)) {
            return true;
          }
          if (item.name) {
            const i = this.cachedViews.indexOf(item.name);
            if (i > -1) {
              this.cachedViews.splice(i, 1);
            }
          }
          if (item.meta?.link) {
            const fi = this.iframeViews.findIndex((v) => v.path === item.path);
            this.iframeViews.splice(fi, 1);
          }
          return false;
        });
        resolve([...this.visitedViews]);
      });
    },
  },
});

export default useTagsViewStore;
