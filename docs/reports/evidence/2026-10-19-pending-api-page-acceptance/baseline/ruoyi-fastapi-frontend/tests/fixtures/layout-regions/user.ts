import { defineStore } from 'pinia';
export default defineStore('layout-fixture-user', {
  state: () => ({ nickName: 'Layout verifier' }),
  actions: { async logOut() {} },
});
