import { createBrowserRouter } from "react-router-dom";

import Index from "./landing/Index.jsx";
import Home from "./landing/pages/Home.jsx";

import Authentication from "./authentication/Authentication.jsx";
import Login from "./authentication/pages/Login.jsx";
import Signup from "./authentication/pages/Signup.jsx";

import User from "./user/User.jsx";
import UserDashboard from "./user/pages/UserDashboard.jsx";

import Admin from "./admin/Admin.jsx";
import AdminDashboard from "./admin/pages/AdminDashboard.jsx";

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
            }
        ]
    },
    {
        path: "/user",
        element: <User />,
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
