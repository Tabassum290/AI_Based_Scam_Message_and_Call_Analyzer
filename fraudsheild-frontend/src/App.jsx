import { Routes, Route } from "react-router-dom";
import Home from "./Pages/Home";
import Dashboard from "./Pages/Dashboard";
import Reports from "./Pages/Reports";
import About from "./Pages/About";
import Layout from "./Pages/Layout";
import Message from "./Pages/Message";


export const App = () => {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="scan" element={<Message/>} />
        <Route path="reports" element={<Reports />} />
        <Route path="about" element={<About />} />
      </Route>
    </Routes>
  );
};
