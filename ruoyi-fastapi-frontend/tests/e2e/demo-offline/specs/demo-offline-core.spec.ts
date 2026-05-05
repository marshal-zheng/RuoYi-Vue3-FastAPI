import { expect, test, type Page } from "@playwright/test";

import {
  confirmMessageBox,
  demoAccount,
  expectNotBlank,
  fillInput,
  fillByTestId,
  goToHashPath,
  seedEditableVersion,
  seedProject,
  submitVisibleDialog,
  testId,
  uniqueName,
} from "../fixtures";
import {
  attachMockNetworkRecorder,
  probeUnhandledApi,
  responseJson,
} from "../network";
import {
  clearBrowserStorage,
  expectDemoOfflineRuntime,
  exportDatasetSnapshot,
  resetDataset,
} from "../runtime";
import { selectors } from "../selectors";

async function login(
  page: Page,
  network: ReturnType<typeof attachMockNetworkRecorder>,
) {
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

async function openProjectList(
  page: Page,
  network: ReturnType<typeof attachMockNetworkRecorder>,
) {
  network.setStep("open project list");
  const seedProjectCard = page.locator(
    testId(selectors.project.card(seedProject.projectId)),
  );
  const alreadyOnProjectList =
    page.url().includes("#/project/project") &&
    (await seedProjectCard.isVisible({ timeout: 1000 }).catch(() => false));

  if (alreadyOnProjectList) {
    return;
  }

  const listResponse = network.waitForMockResponse("project:list");
  await goToHashPath(page, "/project/project");
  await Promise.race([
    listResponse.then(() => undefined),
    seedProjectCard.waitFor({ state: "visible" }).then(() => undefined),
  ]);
  await expect(seedProjectCard).toContainText(seedProject.projectName);
}

test.describe.configure({ mode: "serial" });

test.describe("demo-offline static bundle core flow", () => {
  test("validates login, project writes, versions, topology, simulation, network isolation, and reset", async ({
    page,
    context,
  }) => {
    const network = attachMockNetworkRecorder(page);
    const pageErrors: string[] = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));

    network.setStep("open root");
    const captchaResponse = network.waitForMockResponse("user:captcha");
    await page.goto("/");
    await captchaResponse;
    await expect(page).toHaveURL(/#\/login/);
    await expect(page.getByTestId(selectors.login.username)).toBeVisible();
    await expectDemoOfflineRuntime(page);

    network.setStep("initial dataset reset");
    await resetDataset(page);
    await clearBrowserStorage(page, context);
    await page.reload();
    await expect(page.getByTestId(selectors.login.username)).toBeVisible();
    await login(page, network);

    await openProjectList(page, network);

    network.setStep("create project");
    const projectName = uniqueName("E2E演示工程");
    const updatedProjectName = `${projectName}-已编辑`;
    await page.getByTestId(selectors.project.addButton).click();
    await fillByTestId(page, selectors.project.formName, projectName);
    await fillByTestId(
      page,
      selectors.project.formDesc,
      "demo-offline E2E 新增工程",
    );
    const createResponsePromise = network.waitForMockResponse("project:create");
    await submitVisibleDialog(page, /添加工程/, /下一步/);
    const createResponse = await createResponsePromise;
    const createBody = await responseJson(createResponse);
    const createdProjectId =
      createBody?.projectId ?? createBody?.data?.projectId;
    expect(
      createdProjectId,
      `project:create response should include projectId`,
    ).toBeTruthy();

    await expect(page).toHaveURL(
      new RegExp(`#/project/topo/index/${createdProjectId}`),
    );

    await openProjectList(page, network);
    const createdCard = page.locator(
      testId(selectors.project.card(createdProjectId)),
    );
    await expect(createdCard).toContainText(projectName);

    network.setStep("edit project");
    await createdCard
      .getByTestId(selectors.project.edit(createdProjectId))
      .click();
    const editDialog = page.getByRole("dialog", { name: /编辑工程/ });
    await expect(editDialog).toBeVisible();
    await fillInput(
      editDialog.getByTestId(selectors.project.formName),
      updatedProjectName,
    );
    const updateResponse = network.waitForMockResponse("project:update");
    await editDialog.getByRole("button", { name: /保存/ }).click();
    await updateResponse;
    await expect(createdCard).toContainText(updatedProjectName);

    network.setStep("verify project persistence");
    const persistedList = network.waitForMockResponse("project:list");
    await page.reload();
    await persistedList;
    await expect(createdCard).toContainText(updatedProjectName);

    network.setStep("open version list");
    const versionListResponse = network.waitForMockResponse(
      "project:version:list",
    );
    await goToHashPath(
      page,
      `/project/project-detail/index/${seedProject.projectId}`,
    );
    await versionListResponse;
    await expect(
      page.getByTestId(selectors.version.row(seedEditableVersion.versionId)),
    ).toContainText(seedEditableVersion.versionName);

    network.setStep("clone version");
    const clonedVersionName = uniqueName("E2E克隆版本");
    await page
      .getByTestId(selectors.version.clone(seedEditableVersion.versionId))
      .click();
    const cloneDialog = page.getByRole("dialog", { name: /克隆版本/ });
    await expect(cloneDialog).toBeVisible();
    await fillInput(cloneDialog.getByTestId("version-clone-number"), "V-E2E");
    await fillInput(
      cloneDialog.getByTestId("version-clone-name"),
      clonedVersionName,
    );
    const cloneResponsePromise = network.waitForMockResponse(
      "project:version:clone",
    );
    await cloneDialog.getByRole("button", { name: /克隆/ }).click();
    const cloneResponse = await cloneResponsePromise;
    const cloneBody = await responseJson(cloneResponse);
    const clonedVersionId = cloneBody?.versionId ?? cloneBody?.data?.versionId;
    expect(
      clonedVersionId,
      "project:version:clone response should include versionId",
    ).toBeTruthy();
    await expect(
      page.getByTestId(selectors.version.row(clonedVersionId)),
    ).toContainText(clonedVersionName);

    network.setStep("lock cloned version");
    const lockResponse = network.waitForMockResponse("project:version:lock");
    await page.getByTestId(selectors.version.lock(clonedVersionId)).click();
    await confirmMessageBox(page);
    await lockResponse;
    await expect(
      page.getByTestId(selectors.version.lockStatus(clonedVersionId)),
    ).toContainText("固化");

    network.setStep("save topology");
    const topologyGet = network.waitForMockResponse("project:topology:get");
    const topologyDeviceList = network.waitForMockResponse("device:list");
    await goToHashPath(
      page,
      `/project/topo/index/${seedProject.projectId}?versionId=${seedEditableVersion.versionId}`,
    );
    await topologyGet;
    await topologyDeviceList;
    await expect(page.getByTestId(selectors.topology.page)).toBeVisible();
    await page
      .locator(`${testId(selectors.topology.canvas)} .x6-node`)
      .first()
      .waitFor();
    const topologySave = network.waitForMockResponse("project:topology:save");
    await page.getByTestId(selectors.topology.save).click();
    const topologySaveResponse = await topologySave;
    const topologySaveBody = await responseJson(topologySaveResponse);
    const topologySavedAt = topologySaveBody?.topologyData?.savedAt;
    expect(
      topologySavedAt,
      "topology save response should include savedAt marker",
    ).toEqual(expect.any(String));
    await expect(page).toHaveURL(/#\/project\/project-detail\/index\/1001/);

    network.setStep("verify topology readback");
    const topologyReadback = network.waitForMockResponse(
      "project:topology:get",
    );
    await goToHashPath(
      page,
      `/project/topo/index/${seedProject.projectId}?versionId=${seedEditableVersion.versionId}`,
    );
    const topologyReadbackResponse = await topologyReadback;
    const topologyReadbackBody = await responseJson(topologyReadbackResponse);
    expect(topologyReadbackBody?.topologyData?.savedAt).toBe(topologySavedAt);
    await expect(page.getByTestId(selectors.topology.canvas)).toBeVisible();
    await page
      .locator(`${testId(selectors.topology.canvas)} .x6-node`)
      .first()
      .waitFor();

    network.setStep("open simulation readonly page");
    const simulationSession = network.waitForMockResponse(
      "simulation:session:create-readonly",
    );
    const simulationStatus = network.waitForMockResponse("simulation:status");
    const simulationMessages = network.waitForMockResponse(
      "simulation:messages",
    );
    await goToHashPath(
      page,
      `/project/simulation/index/${seedProject.projectId}?versionId=${seedEditableVersion.versionId}`,
    );
    await simulationSession;
    await simulationStatus;
    await simulationMessages;
    await expect(page.getByTestId(selectors.simulation.page)).toBeVisible();
    await expect(page.getByTestId(selectors.simulation.project)).toContainText(
      seedProject.projectName,
    );
    await expect(page.getByTestId(selectors.simulation.canvas)).toBeVisible();
    await expectNotBlank(page);

    network.setStep("probe missing api");
    await probeUnhandledApi(page);

    network.setStep("reset dataset");
    await resetDataset(page);
    const snapshot = await exportDatasetSnapshot(page);
    expect(JSON.stringify(snapshot)).toContain(seedProject.projectName);
    await clearBrowserStorage(page, context);
    await page.goto("/");
    await expect(page.getByTestId(selectors.login.username)).toBeVisible();
    await login(page, network);
    await openProjectList(page, network);
    await expect(
      page.locator(testId(selectors.project.card(seedProject.projectId))),
    ).toContainText(seedProject.projectName);
    await expect(page.getByText(projectName)).toHaveCount(0);
    await expect(page.getByText(updatedProjectName)).toHaveCount(0);

    network.assertNoRealBackendRequests();
    network.assertCriticalResponsesTagged();
    network.assertNoUnexpectedUnhandledApis();
    network.assertConsumedApisCoveredByCriticalRegistry();
    await network.expectHandlersSeen([
      "user:captcha",
      "user:login",
      "user:csrfToken",
      "user:getInfo",
      "system:getRouters",
      "project:list",
      "project:create",
      "project:update",
      "device:list",
      "project:version:list",
      "project:version:clone",
      "project:version:lock",
      "project:topology:get",
      "project:topology:save",
      "simulation:session:create-readonly",
      "simulation:status",
      "simulation:messages",
      "unhandled-api",
    ]);
    expect(
      pageErrors,
      `Unexpected page errors:\n${pageErrors.join("\n")}`,
    ).toEqual([]);
  });
});
