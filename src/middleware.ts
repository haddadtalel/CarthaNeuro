/**
 * Next.js Middleware for Authentication Protection
 * Protects routes that require authentication
 */
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Define protected routes
const protectedRoutes = [
  '/diagnosis',
  '/data-upload',
  '/models',
  '/profile',
  '/admin',
];

// Define public routes (redirect to these if not authenticated)
const publicRoutes = [
  '/login',
  '/register',
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Get token from localStorage (client-side) - we can't access localStorage in middleware
  // So we'll use cookies or headers set by the client
  const token = request.cookies.get('access_token')?.value;
  const isAuthenticated = !!token;
  
  // Check if current path is protected
  const isProtectedRoute = protectedRoutes.some(route => 
    pathname.startsWith(route)
  );
  
  // Check if current path is public auth route
  const isPublicAuthRoute = publicRoutes.some(route => 
    pathname.startsWith(route)
  );
  
  // If trying to access protected route without authentication
  if (isProtectedRoute && !isAuthenticated) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }
  
  // If trying to access auth routes while already authenticated
  if (isPublicAuthRoute && isAuthenticated) {
    // Redirect to dashboard or intended page
    const redirectPath = request.nextUrl.searchParams.get('redirect') || '/diagnosis';
    const dashboardUrl = new URL(redirectPath, request.url);
    return NextResponse.redirect(dashboardUrl);
  }
  
  // For admin routes, check if user has admin role
  if (pathname.startsWith('/admin')) {
    // Since we can't access localStorage in middleware, we'll let the client-side handle admin checks
    // This is a limitation of Next.js middleware - it runs on the server side
    // The client-side authentication context will handle role-based access control
  }
  
  return NextResponse.next();
}

// Configure which routes to run middleware on
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder files
     */
    '/((?!api|_next/static|_next/image|favicon.ico|.*\\..*|public/).*)',
  ],
};