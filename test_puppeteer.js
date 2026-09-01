const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto('https://patchproofv101-lmp0t4p57-manav-b3d8.vercel.app');
  await page.waitForSelector('#section-analyze');
  const html = await page.$eval('#section-analyze', el => el.outerHTML);
  console.log(html);
  await browser.close();
})();
