const MAP = {
  '/index.html': '/', '/models.html': '/models', '/model-detail.html': '/model-detail',
  '/trends.html': '/trends', '/route.html': '/route', '/quiz.html': '/quiz',
  '/stack.html': '/stack', '/lab.html': '/lab', '/pricing.html': '/pricing',
  '/how-we-score.html': '/how-we-score', '/ecosystem.html': '/ecosystem',
  '/login.html': '/login', '/register.html': '/register', '/account.html': '/account',
  '/reset.html': '/reset', '/merge.html': '/merge', '/admin-dashboard.html': '/admin-dashboard',
};
export const onRequest = (context, next) => {
  const req = context.request;
  const url = new URL(req.url);
  const host = req.headers.get('host') || 'routevault.ai';
  const proto = req.headers.get('x-forwarded-proto') || 'https';
  const origin = `${proto}://${host}`;
  const path = url.pathname;
  if (path === '/model-detail.html') {
    const id = url.searchParams.get('id');
    return Response.redirect(`${origin}${id ? `/model/${id}` : '/models'}`, 301);
  }
  if (MAP[path]) return Response.redirect(`${origin}${MAP[path]}`, 301);
  return next();
};
