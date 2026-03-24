import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import {
  Box,
  Button,
  Text,
  Stack,
  Modal,
  Group,
  Title,
  Flex,
  TextInput,
  Progress,
  rem,
  Select,
  useMantineColorScheme,
} from "@mantine/core";
import { FaCheck, FaTimes } from 'react-icons/fa';
import { notifications } from '@mantine/notifications';
import { useMediaQuery } from "@mantine/hooks";
import { createCustomRole } from "../../api/Roles";

function getProgress(inputs) {
  const filledInputs = inputs.filter((input) => input.length > 0);
  return (filledInputs.length / inputs.length) * 100;
}

const CreateCustomRolePage = () => {
  const { colorScheme } = useMantineColorScheme();
  const isDark = colorScheme === "dark";
  const xIcon = <FaTimes style={{ width: rem(20), height: rem(20) }} />;
  const checkIcon = <FaCheck style={{ width: rem(20), height: rem(20) }} />;

  const [roleDetails, setRoleDetails] = useState({
    name: "",
    full_name: "",
    type: "",
    basic: false,
  });

  const progress = getProgress([roleDetails.name, roleDetails.full_name, roleDetails.type]);
  const [isOpen, setIsOpen] = useState(false);
  const [validationModalOpen, setValidationModalOpen] = useState(false);
  const submitButtonRef = useRef(null);
  const confirmButtonRef = useRef(null);

  const matches = useMediaQuery('(min-width: 768px)');

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!roleDetails.name || !roleDetails.full_name || !roleDetails.type) {
      setValidationModalOpen(true);
      return;
    }

    try {
      await createCustomRole(roleDetails);
      // await axios.post(
      //   "http://127.0.0.1:8000/api/create-role/",
      //   roleDetails,
      //   {
      //     headers: {
      //       "Content-Type": "application/json",
      //     },
      //   }
      // );

      notifications.show({
        icon: checkIcon,
        title: "Success",
        position: "top-center",
        withCloseButton: true,
        autoClose: 5000,
        message: "Role created successfully.",
        color: "green",
      });

      setRoleDetails({
        name: "",
        full_name: "",
        type: "",
        basic: false,
      });

      setIsOpen(false);

    } catch (err) {
      const errorMessage = err.response
        ? `Error: ${JSON.stringify(err.response.data)}`
        : err.request
          ? "No response received from the server"
          : `Error: ${err.message}`;

      notifications.show({
        icon: xIcon,
        title: "Error",
        position: "top-center",
        withCloseButton: true,
        autoClose: 5000,
        message: errorMessage,
        color: "red",
      });
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setRoleDetails((prevRoleDetails) => ({
      ...prevRoleDetails,
      [name]: value,
    }));
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      if (isOpen) {
        confirmButtonRef.current.click();
      } else {
        submitButtonRef.current.click();
      }
    }
  };

  useEffect(() => {
    document.addEventListener("keydown", handleKeyPress);
    return () => {
      document.removeEventListener("keydown", handleKeyPress);
    };
  }, [isOpen]);

  return (
    <Box
      p="lg"
      style={{
        backgroundColor: isDark ? "#1a1b1e" : "#f7f7f7",
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        flexDirection: "column",
        gap: "5rem",
      }}
    >
      {/* Title Button */}
      <Button
        variant="gradient"
        size="xl"
        radius="xs"
        gradient={{ from: "blue", to: "cyan", deg: 90 }}
        w={matches && "500px"}
        style={{
          fontSize: "1.8rem",
          lineHeight: 1.2,
          marginBottom: "1rem",  // Space below the button
        }}
      >
        <Title
          order={1}
          align="center"
          style={{
            fontSize: "1.25rem",
            wordBreak: "break-word",
          }}
        >
          Create Custom Role
        </Title>
      </Button>

      <Stack
        spacing="xl"
        align="center"
        style={{
          maxWidth: "600px",
          width: "100%",
          padding: "1rem",
        }}
      >
        {/* Form with Progress Bar */}
        <Flex
          direction="column"
          gap="lg"
          p="xl"
          style={{
            border: isDark ? "2px solid #444" : "2px solid #ccc",
            backgroundColor: isDark ? "#2c2e33" : "#fff",
            borderRadius: "10px",
            boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
            maxWidth: "500px",
            width: "100%",
            padding: "1.5rem",
          }}
        >
          <Progress
            value={progress}
            size="lg"
            color={progress < 50 ? "red" : progress < 75 ? "orange" : "teal"}
          />

          <Stack spacing="lg">
            <TextInput
              label="Role Name"
              name="name"
              placeholder="Enter role name"
              value={roleDetails.name}
              onChange={handleChange}
              required
              radius="md"
              styles={(theme) => ({
                input: {
                  border: `2px solid ${theme.colors.gray[4]}`,
                },
              })}
            />

            <TextInput
              label="Full Name"
              name="full_name"
              placeholder="Enter full name of the role"
              value={roleDetails.full_name}
              onChange={handleChange}
              required
              radius="md"
              styles={(theme) => ({
                input: {
                  border: `2px solid ${theme.colors.gray[4]}`,
                },
              })}
            />

            <Select
              label="Type"
              name="type"
              placeholder="Select type of the role"
              value={roleDetails.type}
              onChange={(value) => setRoleDetails({ ...roleDetails, type: value })}
              data={[
                { value: 'academic', label: 'Academic Designation' },
                { value: 'administrative', label: 'Administrative Designation' },
              ]}
            />

            <Select
              label="Basic"
              name="basic"
              placeholder="Select whether the role is basic"
              value={roleDetails.basic ? "true" : "false"}
              onChange={(value) => setRoleDetails({ ...roleDetails, basic: value=="true"? true: false })}
              data={[
                { value: "false", label: 'False' },
                { value: "true", label: 'True' },
              ]}
            />

            <Button
              ref={submitButtonRef}
              color="blue"
              onClick={() => setIsOpen(true)}
              fullWidth
              mt="md"
            >
              Create Role
            </Button>
          </Stack>
        </Flex>

        {/* Confirmation Modal */}
        <Modal
          opened={isOpen}
          onClose={() => setIsOpen(false)}
          title="Confirm Role Creation"
        >
          <Text>Are you sure you want to create this custom role?</Text>
          <Group position="right" mt="md">
            <Button variant="default" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            <Button ref={confirmButtonRef} color="blue" onClick={handleSubmit}>
              Confirm
            </Button>
          </Group>
        </Modal>

        {/* Validation Modal for empty fields */}
        <Modal
          opened={validationModalOpen}
          onClose={() => setValidationModalOpen(false)}
          title="Incomplete Fields"
        >
          <Text>You need to fill in all the fields before submitting the form.</Text>
          <Group position="right" mt="md">
            <Button onClick={() => setValidationModalOpen(false)}>OK</Button>
          </Group>
        </Modal>
      </Stack>
    </Box>
  );
};

export default CreateCustomRolePage;
