Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
window.chrome = {runtime: {}};
Object.defineProperty(navigator, 'languages', {get: () => ['es-ES', 'es']});
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
