import React, { useState, useEffect } from "react";
import {
  TextInput,
  Select,
  Button,
  Grid,
  Group,
  Box,
  NumberInput,
  Radio,
  rem,
  Title,
  Divider,
  Progress,
  Flex,
  Paper,
  Stack,
  FileInput,
  useMantineColorScheme,
} from "@mantine/core";
import { FaCheck, FaDiceD6, FaTimes } from "react-icons/fa";
import { notifications, showNotification } from "@mantine/notifications";
import { DateInput, YearPickerInput } from "@mantine/dates";
import { useMediaQuery } from "@mantine/hooks";
import { getAllDepartments, getAllBatches } from '../../api/Roles';
import { createStudent, bulkUploadUsers, downloadSampleCSV } from "../../api/Users";

const StudentCreationPage = () => {
  const { colorScheme } = useMantineColorScheme();
  const isDark = colorScheme === "dark";
  
  const xIcon = <FaTimes style={{ width: rem(20), height: rem(20) }} />;
  const checkIcon = <FaCheck style={{ width: rem(20), height: rem(20) }} />;

  const [formValues, setFormValues] = useState({
    username: "",
    first_name: "",
    last_name: "",
    sex: "",
    category: "",
    father_name: "",
    mother_name: "",
    programme: "",
    batch: "",
    department: '',
    title: '',
    designation: '',
    dob: null,
    phone: '',
    address: '',
  });

  const [progress, setProgress] = useState(0);
  const [departments, setDepartments] = useState([]);
  const [batches, setBatches] = useState([]);
  const [file, setFile] = useState(null);

  useEffect(() => {
    const totalFields = Object.keys(formValues).length;
    const filledFields = Object.values(formValues).filter(
      (value) => value
    ).length;
    setProgress((filledFields / totalFields) * 100);
  }, [formValues]);

  const handleChange = (field, value) => {
    setFormValues((prev) => ({
      ...prev,
      [field]: field === "hall_no" ? parseInt(value, 10) || 0 : value,
    }));
  };

  const handleFileSubmit = (file) => {
    setFile(file);
  }

  const fetchDepartments = async () => {
      try {
          let all_departments = [];
          const response = await getAllDepartments();
          for(let i=0; i<response.length; i++){
              all_departments[i] = {value: `${response[i].id}`, label: response[i].name}
          }
          setDepartments(all_departments);
      } catch (error) {
          showNotification({
              title: 'Error',
              icon: xIcon,
              position: "top-center",
              withCloseButton: true,
              message: 'An error occurred while fetching departments.',
              color: 'red',
          });
      }
  }

  const fetchBatches = async () => {
    try {
        let all_batches = [];
        const response = await getAllBatches();
        for(let i=0; i<response.length; i++){
            all_batches[i] = `${response[i].year}`
        }
        setBatches(all_batches);
    } catch (error) {
        showNotification({
            title: 'Error',
            icon: xIcon,
            position: "top-center",
            withCloseButton: true,
            message: 'An error occurred while fetching batches.',
            color: 'red',
        });
    }
  }

  const downloadCSV = (url, filename) => {
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    console.log("Form Submitted", formValues);

    try {
      let response;
      if(file){
        const formData = new FormData();
        formData.append('file', file);
        response = await bulkUploadUsers(formData);
        setFile(null);
      }
      else response = await createStudent(formValues);

      if(response.skipped_users_count > 0){
        const csvUrl = URL.createObjectURL(new Blob([response.skipped_users_csv], {type: 'text/csv'}));
        downloadCSV(csvUrl, 'skipped_users.csv');
      }
      showNotification({
        icon: checkIcon,
        title: "Success",
        position: "top-center",
        withCloseButton: true,
        autoClose: 5000,
        message: `${response.created_users.length} Student has been Created Successfully.\n${response.skipped_users_count ? `${response.skipped_users_count} User skipped.` : ''}`,
        color: "green",
      });
      setFormValues({
        username: "",
        first_name: "",
        last_name: "",
        sex: "",
        category: "",
        father_name: "",
        mother_name: "",
        programme: "",
        batch: "",
        department: '',
        title: '',
        designation: '',
        dob: null,
        phone: '',
        address: '',
      });
    } catch (err) {
      const errorMessage = err.response
        ? `${JSON.stringify(err.response.data.error) || JSON.stringify(err.response.data.data) || JSON.stringify(err.response.data.message)}`
        : err.request
        ? "No response received from the server"
        : `${err.message}`;

      showNotification({
        title: "Error",
        icon: xIcon,
        position: "top-center",
        withCloseButton: true,
        message: errorMessage,
        color: "red",
      });
    }
  };

  useEffect(() => {
    fetchDepartments();
    fetchBatches();
  }, []);

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        handleSubmit();
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [formValues]);

  const matches = useMediaQuery("(min-width: 768px)");

  return (
    <Box maw={700} mx="auto" p="lg" style={{ backgroundColor: isDark ? '#1a1b1e' : '#fff' }}>
      <Paper shadow="xl" radius="lg" p="xl" style={{ 
        backgroundColor: isDark ? '#2c2e33' : '#fdfdfd',
        color: isDark ? '#fff' : '#000'
      }}>
        <Flex
          gap="md"
          justify="center"
          align="center"
          direction="row"
          wrap="wrap"
        >
          <Button
            variant="gradient"
            size="xl"
            radius="xs"
            gradient={{ from: "blue", to: "cyan", deg: 90 }}
            w={matches && "500px"}
            style={{
              fontSize: "1.8rem",
              lineHeight: 1.2,
              marginBottom: "1rem",
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
              Add Student
            </Title>
          </Button>
        </Flex>

        <Divider my="sm" style={{ borderColor: isDark ? '#444' : '#e0e0e0' }} />

        {/* Progress Bar */}
        <Progress value={progress} color="blue" mb="md" />

        <Grid gutter="md">
          {/* Roll No */}
          <Grid.Col span={6}>
            <TextInput
              label="Roll Number"
              placeholder="Enter roll number"
              value={formValues.roll_no}
              onChange={(e) => handleChange("username", e.target.value)}
              required
            />
          </Grid.Col>

          {/* First Name */}
          <Grid.Col span={6}>
            <TextInput
              label="First Name"
              placeholder="Enter first name"
              value={formValues.first_name}
              onChange={(e) => handleChange("first_name", e.target.value)}
              required
            />
          </Grid.Col>

          {/* Last Name */}
          <Grid.Col span={6}>
            <TextInput
              label="Last Name"
              placeholder="Enter last name / NA"
              value={formValues.last_name}
              onChange={(e) => handleChange("last_name", e.target.value)}
              required
            />
          </Grid.Col>

          {/* Title */}
          <Grid.Col span={6}>
            <Select
              label="Title"
              placeholder="Select title"
              data={['Dr.', 'Mr.', 'Mrs.', 'Ms.']}
              value={formValues.title}
              onChange={(value) => handleChange('title', value)}
              />
          </Grid.Col>         

          {/* Department */}
          <Grid.Col span={12}>
            <Select
              label="Department"
              placeholder="Enter department"
              data={departments}
              value={`${formValues.department}`}
              onChange={(value) => handleChange('department', Number(value))}
              />
          </Grid.Col>  

          {/* Gender */}
          <Grid.Col span={12}>
            <Radio.Group
              label="Gender"
              value={formValues.sex}
              onChange={(value) => handleChange("sex", value)}
              required
            >
              <Group spacing="sm" position="apart" mt="xs">
                <Radio value="male" label="Male" />
                <Radio value="female" label="Female" />
                {/* <Radio value="other" label="Other" /> */}
              </Group>
            </Radio.Group>
          </Grid.Col>

          {/* Category */}
          <Grid.Col span={12}>
            <Select
              label="Category"
              placeholder="Select category"
              data={["GEN", "OBC", "SC", "ST"]}
              value={formValues.category}
              onChange={(value) => handleChange("category", value)}
              required
            />
          </Grid.Col>

          {/* Father's Name */}
          <Grid.Col span={6}>
            <TextInput
              label="Father's Name"
              placeholder="Enter father's name"
              value={formValues.father_name}
              onChange={(e) => handleChange("father_name", e.target.value)}
              required
            />
          </Grid.Col>

          {/* Mother's Name */}
          <Grid.Col span={6}>
            <TextInput
              label="Mother's Name"
              placeholder="Enter mother's name"
              value={formValues.mother_name}
              onChange={(e) => handleChange("mother_name", e.target.value)}
              required
            />
          </Grid.Col>

          <Grid.Col span={6}>
            <Select
              label="Programme"
              placeholder="Select programme"
              data={['B.Tech', 'B.Des', 'M.Tech', 'M.Des', 'PhD']}
              value={formValues.programme}
              onChange={(value) => handleChange("programme", value)}
              required
            />
          </Grid.Col>

          <Grid.Col span={6}>
            <Select
              label="Batch"
              placeholder="Select batch"
              data={batches}
              value={`${formValues.batch}`}
              onChange={(value) => handleChange("batch", Number(value))}
              required
            />
          </Grid.Col>
        </Grid>
        <Flex
          gap="md"
          justify="center"
          align="center"
          direction="row"
          wrap="wrap"
          mt="xl"
        >
          <Button onClick={handleSubmit} color="blue" size="md">
            Add Student
          </Button>
        </Flex>

        <Divider
          mt={"20px"}
          style={{ borderColor: isDark ? '#444' : '#e0e0e0' }}
          labelPosition="center"
          label={
            <>
              <FaDiceD6 size={12} />
            </>
          }
        />

        <Stack justify="center" align="center" mt={'20px'}>
          <Title
            order={1}
            sx={{
              fontSize: { base: 'lg', sm: 'xl' },
              lineHeight: 1.2,
              wordBreak: 'break-word',
            }}
          >
            Through CSV
          </Title>
          <FileInput
            value={file}
            onChange={handleFileSubmit}
            size="md"
            radius="xs"
            placeholder="Upload CSV"
            w={"50%"}
            styles={{
              input: { 
                backgroundColor: isDark ? '#373a40' : '#fff',
                color: isDark ? '#fff' : '#000',
                borderColor: isDark ? '#444' : '#ced4da'
              }
            }}
          />
          <Button
            onClick={handleSubmit}
            w={'50%'}
            mt={'10px'} 
            size="md" 
          >
            Create Students
          </Button>

          <Button
            variant="light"
            color="gray"
            onClick={downloadSampleCSV}
          >
            Download Sample CSV
          </Button>
        </Stack>
      </Paper>
    </Box>
  );
};

export default StudentCreationPage;
