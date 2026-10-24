import { expect, test } from "@playwright/test";

import { fillByTestId, submitVisibleDialog, uniqueName } from "../../fixtures";
import { attachMockNetworkRecorder } from "../../network";
import {
  activateOverlays,
  bootstrapOverlays,
  expectDemoOfflineRuntime,
  expectOverlayState,
  resetOverlays,
} from "../../runtime";
import { selectors } from "../../selectors";
import { loginDemo, openRoot } from "../fixtures";

test.describe("demo-offline project page states", () => {
  test("renders project list empty state from bootstrap overlay", async ({
    page,
    context,
  }) => {
    await bootstrapOverlays(context, ["project-list-empty"]);
    const network = attachMockNetworkRecorder(page);

    await openRoot(page, network);
    await expectDemoOfflineRuntime(page);
    const emptyResponse = network.waitForOverlayResponse("project-list-empty");
    await loginDemo(page, network);
    await emptyResponse;

    await expectOverlayState(page, ["project-list-empty"]);
    await expect(page.getByText("暂无工程")).toBeVisible();
    await expect(page.getByTestId("project-empty-add-button")).toBeVisible();

    await resetOverlays(page);
    await expectOverlayState(page, []);
    network.assertOverlayResponsesTagged();
    network.assertNoRealBackendRequests();
  });

  test("keeps the create dialog open on project write error overlay", async ({
    page,
  }) => {
    const network = attachMockNetworkRecorder(page);
    await openRoot(page, network);
    await expectDemoOfflineRuntime(page);
    await loginDemo(page, network);

    network.setStep("activate project create error");
    await activateOverlays(page, ["project-create-500"]);
    await expectOverlayState(page, ["project-create-500"]);

    await page.getByTestId(selectors.project.addButton).click();
    const failedProjectName = uniqueName("overlay-error-project");
    await fillByTestId(page, selectors.project.formName, failedProjectName);
    await fillByTestId(
      page,
      selectors.project.formDesc,
      "page-state overlay write error",
    );
    const createResponse = network.waitForOverlayResponse("project-create-500");
    await submitVisibleDialog(page, /添加工程/, /下一步/);
    const response = await createResponse;

    expect(response.status()).toBe(500);
    await expect(page.getByTestId(selectors.project.listPage)).toBeVisible();
    await expect(page.getByText(failedProjectName)).toHaveCount(0);
    network.assertOverlayResponsesTagged();
    network.assertNoRealBackendRequests();
  });
});
