import { createBrowserRouter } from "react-router-dom";
import { Navigate } from "react-router-dom";

import Index from "./landing/Index.jsx";
import Home from "./landing/pages/Home.jsx";

import Authentication from "./authentication/Authentication.jsx";
import Login from "./authentication/pages/Login.jsx";
import Signup from "./authentication/pages/Signup.jsx";

import User from "./user/User.jsx";
import UserDashboard from "./user/pages/UserDashboard.jsx";

import Admin from "./admin/Admin.jsx";
import AdminDashboard from "./admin/pages/AdminDashboard.jsx";
import { useNavigate } from "react-router-dom";

const LogoutButton = () => {
    const navigate = useNavigate();

    const handleLogout = async () => {
        // Optionally notify backend
        await fetch("http://127.0.0.1:5000/api/auth/logout", { method: "POST" });

        console.log("Local: ", localStorage);
        // Remove token and user info
        localStorage.removeItem("token");
        localStorage.removeItem("uid");
        localStorage.removeItem("email");
        localStorage.removeItem("username");


        // Redirect to login
        navigate("/auth/login");
    };

    return (
        <button onClick={handleLogout}>
            Logout
        </button>
    );
};

const RequireAuth = ({ children }) => {
    const token = localStorage.getItem("token");
    if (!token) {
        return <Navigate to="/auth/login" replace />;
    }
    return children;
};

const router = createBrowserRouter([
    {
        path: "/",
        element: <Index />,
        children: [
            {
                path: "",
                element: <Home />
            }
        ]
    },
    {
        path: "/auth",
        element: <Authentication />,
        children: [
            {
                path: "login",
                element: <Login />
            },
            {
                path: "signup",
                element: <Signup />
            },
            {
                path: "logout",
                element: <LogoutButton />,
            }
        ]
    },
    {
        path: "/user",
        element: (
            <RequireAuth>
                <User />
            </RequireAuth>
        ),
        children: [
            {
                path: "dashboard",
                element: <UserDashboard />
            }
        ]
    },
    {
        path: "/admin",
        element: <Admin />,
        children: [
            {
                path: "dashboard",
                element: <AdminDashboard />
            }
        ]
    }
]);

export default router;
