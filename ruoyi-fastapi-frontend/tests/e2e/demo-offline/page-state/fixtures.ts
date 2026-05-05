import { expect, type Page } from "@playwright/test";

import {
  demoAccount,
  expectNotBlank,
  fillByTestId,
  goToHashPath,
  seedEditableVersion,
  seedProject,
} from "../fixtures";
import type { attachMockNetworkRecorder } from "../network";
import { selectors } from "../selectors";

type NetworkRecorder = ReturnType<typeof attachMockNetworkRecorder>;

export { seedEditableVersion, seedProject };

export async function loginDemo(page: Page, network: NetworkRecorder) {
  network.setStep("login");
  const loginResponse = network.waitForMockResponse("user:login");
  const csrfResponse = network.waitForMockResponse("user:csrfToken");
  const infoResponse = network.waitForMockResponse("user:getInfo");
  const routersResponse = network.waitForMockResponse("system:getRouters");

  await fillByTestId(page, selectors.login.username, demoAccount.username);
  await fillByTestId(page, selectors.login.password, demoAccount.password);
  await page.getByTestId(selectors.login.submit).click();

  await loginResponse;
  await csrfResponse;
  await infoResponse;
  await routersResponse;
  await expect(page).toHaveURL(/#\/project\/project/);
  await expectNotBlank(page);
}

export async function openRoot(page: Page, network: NetworkRecorder) {
  network.setStep("open root");
  const captchaResponse = network.waitForMockResponse("user:captcha");
  await page.goto("/");
  await captchaResponse;
  await expect(page).toHaveURL(/#\/login/);
  await expect(page.getByTestId(selectors.login.username)).toBeVisible();
}

export async function openProjectDetail(page: Page, network: NetworkRecorder) {
  network.setStep("open project detail");
  const projectResponse = network.waitForMockResponse("project:get");
  await goToHashPath(
    page,
    `/project/project-detail/index/${seedProject.projectId}`,
  );
  await projectResponse;
  await expect(page.getByTestId("project-detail-page")).toBeVisible();
}
