import { expect, type Locator, type Page } from "@playwright/test";

export const demoAccount = {
  username: "admin",
  password: "admin123",
};

export const seedProject = {
  projectId: 1001,
  projectName: "联合指挥中心演示项目",
};

export const seedEditableVersion = {
  versionId: 2002,
  versionName: "V1.1 评审版",
};

export function uniqueName(prefix: string) {
  return `${prefix}-${Date.now().toString(36)}`;
}

export function testId(id: string) {
  return `[data-testid="${id}"]`;
}

export async function goToHashPath(page: Page, path: string) {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  await page.goto(`/#${normalized}`);
}

export async function fillInput(locator: Locator, value: string) {
  const target = locator.first();
  const tagName = await target.evaluate((element) =>
    element.tagName.toLowerCase(),
  );

  if (tagName === "input" || tagName === "textarea") {
    await target.fill(value);
    return;
  }

  await target.locator("input, textarea").first().fill(value);
}

export async function fillByTestId(page: Page, id: string, value: string) {
  await fillInput(page.getByTestId(id), value);
}

export async function expectNotBlank(page: Page) {
  await expect(page.locator("#app")).toBeVisible();
  const documentBody = page.locator("html > body");
  await expect(documentBody).not.toContainText("404");
  await expect(documentBody).not.toContainText("401");
}

export async function submitVisibleDialog(
  page: Page,
  name: RegExp,
  buttonName: RegExp,
) {
  const dialog = page.getByRole("dialog", { name });
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: buttonName }).click();
}

export async function confirmMessageBox(page: Page) {
  const dialog = page
    .getByRole("dialog")
    .filter({ hasText: /确定|确认/ })
    .last();
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: /^确定$/ }).click();
}
