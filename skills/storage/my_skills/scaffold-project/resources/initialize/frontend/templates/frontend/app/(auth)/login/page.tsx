import { LoginForm } from "@/components/auth/login-form";

/**
 * Login Page — renders OAuth + email/password form.
 *
 * Basic SEO meta for this public-facing page.
 */
export const metadata = {
    title: "Sign In",
    description: "Sign in to your account",
};

export default function LoginPage() {
    return <LoginForm />;
}
